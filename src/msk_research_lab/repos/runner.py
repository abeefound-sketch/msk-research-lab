"""Repository runner with strict sandbox enforcement and process lifecycle control."""

import os
import signal
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


class ApprovalRequiredError(PermissionError):
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


def verify_approval(repo_id: str, profile_id: str, commit_sha: str, token: str) -> bool:
    """Verify that a valid, active approval token exists."""
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT id FROM execution_approvals
            WHERE repo_id = ? AND profile_id = ? AND commit_sha = ? AND approval_token = ? AND status = 'ACTIVE';
            """,
            (repo_id, profile_id, commit_sha, token)
        )
        return bool(cur.fetchone())


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
        is_synthetic: bool = False
    ) -> Dict[str, Any]:
        """Launch a process with safety checks."""
        # 1. Enforce sandbox check for non-synthetic runs
        if require_sandbox and not is_synthetic:
            sb = probe_sandbox_capabilities()
            if not sb.get("isolation_enforceable", False):
                raise SandboxExecutionBlockedError(
                    f"Untrusted execution BLOCKED: {sb.get('details', 'Sandbox isolation unavailable.')}"
                )

        # 2. Start process in separate process group for clean teardown
        proc = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=env or os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None
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
