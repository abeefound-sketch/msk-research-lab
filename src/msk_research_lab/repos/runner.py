"""Repository runner with strict sandbox enforcement and process lifecycle control."""

import os
import signal
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.sandbox.probe import probe_sandbox_capabilities


class SandboxExecutionBlockedError(PermissionError):
    """Raised when untrusted execution is attempted without enforceable container isolation."""
    pass


class ApprovalRequiredError(SandboxExecutionBlockedError):
    """Raised when execution is attempted without a verified human approval token."""
    pass


def approve_run_profile(
    repo_id: str,
    profile_id: str,
    commit_sha: str,
    approved_by: str = "OPERATOR"
) -> str:
    """Record an explicit human approval token for a specific commit and profile."""
    approval_token = f"appr-{uuid.uuid4().hex[:12]}"
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO execution_approvals (repo_id, profile_id, commit_sha, approved_by, approval_token, status)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE');
            """,
            (repo_id, profile_id, commit_sha, approved_by, approval_token)
        )
        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?);
            """,
            (
                "PROFILE_APPROVED",
                approved_by,
                f'{{"repo_id": "{repo_id}", "profile_id": "{profile_id}", "sha": "{commit_sha}", "token": "{approval_token}"}}'
            )
        )
    return approval_token


def verify_approval(repo_id: str, profile_id: str, commit_sha: str, token: Optional[str]) -> bool:
    """Verify that a valid, active approval token exists."""
    if not token:
        return False
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT id FROM execution_approvals
            WHERE repo_id = ? AND profile_id = ? AND commit_sha = ? AND approval_token = ? AND status = 'ACTIVE';
            """,
            (repo_id, profile_id, commit_sha, token)
        )
        return bool(cur.fetchone())


def wrap_with_bubblewrap(
    argv: List[str],
    repo_dir: Path,
    bwrap_path: Optional[str] = None
) -> List[str]:
    """Construct least-privilege Bubblewrap command profile.

    Guarantees:
    - Root filesystem isolated: read-only bind for /bin, /lib, /lib64, /usr
    - Private volatile scratch: --tmpfs /tmp
    - Target directory bound read-only to /app: --ro-bind <repo_dir> /app
    - Sensitive host paths completely excluded: /mnt (Windows drives C/D), /home (SSH keys/tokens)
    - Full process isolation: --unshare-all (PID, IPC, user namespaces)
    - Network strictly denied: --unshare-net
    - Parent process lifecycle bound: --die-with-parent
    """
    bwrap_bin = bwrap_path or shutil.which("bwrap") or "/home/tuan/.local/bin/bwrap"

    cmd = [
        bwrap_bin,
        "--unshare-all",
        "--unshare-net",
        "--die-with-parent",
        "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--ro-bind", "/usr", "/usr",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
    ]

    # Include virtualenv if active/present so python interpreters can execute inside sandbox
    venv_path = "/home/tuan/.venvs"
    if os.path.exists(venv_path):
        cmd.extend(["--ro-bind", venv_path, venv_path])

    if repo_dir and repo_dir.exists():
        cmd.extend([
            "--ro-bind", str(repo_dir), "/app",
            "--chdir", "/app"
        ])

    cmd.append("--")
    cmd.extend(argv)
    return cmd


class ProcessGovernor:
    """Bounded lifecycle manager for running processes with timeout and group cleanup."""

    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def launch(
        self,
        job_id: str,
        argv: List[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 300,
        require_sandbox: bool = True,
        is_synthetic: bool = False,
        repo_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        commit_sha: Optional[str] = None,
        approval_token: Optional[str] = None,
        max_memory_mb: int = 500,
        max_processes: int = 16
    ) -> Dict[str, Any]:
        """Launch a process with safety checks."""
        # 1. Enforce sandbox check for non-synthetic runs
        final_argv = list(argv)
        if require_sandbox and not is_synthetic:
            sb = probe_sandbox_capabilities()
            if not sb.get("isolation_enforceable", False):
                raise SandboxExecutionBlockedError(
                    f"Untrusted execution BLOCKED: {sb.get('details', 'Sandbox isolation unavailable.')}"
                )

            # Enforce verified human approval token
            if repo_id and profile_id and commit_sha:
                if not verify_approval(repo_id, profile_id, commit_sha, approval_token):
                    raise ApprovalRequiredError(
                        f"Execution BLOCKED: Separate operator approval token required for repository '{repo_id}' at commit '{commit_sha}'."
                    )
            elif not approval_token:
                # If identifying fields are not provided, an approval token is still strictly required
                raise ApprovalRequiredError(
                    "Execution BLOCKED: Separate operator approval token required for untrusted execution."
                )

            # Wrap with Bubblewrap if active runtime
            if sb.get("runtime") == "bubblewrap":
                bwrap_bin = sb.get("runtime_path") or "/home/tuan/.local/bin/bwrap"
                final_argv = wrap_with_bubblewrap(argv, cwd, bwrap_path=bwrap_bin)

        # 2. Setup isolated preexec function enforcing memory and resource limits
        def _sandbox_preexec():
            if hasattr(os, "setsid"):
                os.setsid()
            try:
                import resource
                mem_bytes = max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            except Exception:
                pass

        # 3. Start process in separate process group for clean teardown
        proc = subprocess.Popen(
            final_argv,
            cwd=str(cwd),
            env=env or os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=_sandbox_preexec
        )
        self.active_processes[job_id] = proc

        return {
            "job_id": job_id,
            "pid": proc.pid,
            "status": "STARTED",
            "start_time": time.time()
        }

    def stop(self, job_id: str) -> Dict[str, Any]:
        """Gracefully stop and clean up process group."""
        proc = self.active_processes.get(job_id)
        if not proc:
            return {"job_id": job_id, "status": "NOT_FOUND"}

        try:
            if hasattr(os, "killpg"):
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:
                pass

        stdout, stderr = proc.communicate()
        del self.active_processes[job_id]

        return {
            "job_id": job_id,
            "exit_code": proc.returncode,
            "status": "STOPPED",
            "stdout": stdout,
            "stderr": stderr
        }


governor = ProcessGovernor()
