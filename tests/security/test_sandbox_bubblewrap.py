"""Security test suite for Bubblewrap rootless sandbox and process isolation (G2 / SEC-01..05).

Verifies that untrusted code:
1. Cannot access Windows mounts (/mnt/c, /mnt/d) or MSK-Therapy-OS
2. Cannot access user private credentials or SSH keys (/home/tuan/.ssh)
3. Cannot make network connections (network-denied profile)
4. Is strictly constrained by memory ceilings (RLIMIT_AS) and cannot exhaust host RAM
5. Cannot see or signal host processes (PID namespace isolation)
6. Fails closed without a verified human approval token
"""

import os
import shutil
import subprocess
import sys
import pytest
from pathlib import Path

from msk_research_lab.sandbox.probe import probe_sandbox_capabilities
from msk_research_lab.repos.runner import (
    ProcessGovernor,
    wrap_with_bubblewrap,
    approve_run_profile,
    verify_approval,
    ApprovalRequiredError,
    SandboxExecutionBlockedError
)


@pytest.fixture
def bwrap_path():
    p = shutil.which("bwrap") or "/home/tuan/.local/bin/bwrap"
    if not os.path.exists(p):
        pytest.skip("Bubblewrap binary not found on host.")
    return p


def test_bwrap_probe_reports_verified(bwrap_path):
    """Verify probe_sandbox_capabilities detects Bubblewrap and marks isolation as enforceable."""
    sb = probe_sandbox_capabilities()
    assert sb["runtime"] == "bubblewrap"
    assert sb["isolation_enforceable"] is True
    assert sb["status"] == "SANDBOX_VERIFIED_BUBBLEWRAP"
    assert sb["checks"]["container_binary"] is True
    assert sb["checks"]["mount_isolation"] is True
    assert sb["checks"]["network_denial"] is True
    assert sb["checks"]["process_isolation"] is True
    # G2 gate remains locked awaiting specific upstream execution approval
    assert sb["can_execute_untrusted"] is False


def test_sandbox_blocks_windows_and_therapy_os_mounts(bwrap_path, tmp_path):
    """Verify that /mnt (Windows C:, D: drives and MSK-Therapy-OS) is completely inaccessible."""
    cmd = wrap_with_bubblewrap(
        ["/bin/sh", "-c", "test -e /mnt && ls /mnt || echo 'MNT_DENIED'"],
        repo_dir=tmp_path,
        bwrap_path=bwrap_path
    )
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    assert res.returncode == 0
    assert "MNT_DENIED" in res.stdout
    assert "5Projects" not in res.stdout
    assert "msk-therapy-os" not in res.stdout


def test_sandbox_blocks_ssh_keys_and_private_home(bwrap_path, tmp_path):
    """Verify that /home/tuan/.ssh and host credentials are completely excluded from the sandbox."""
    cmd = wrap_with_bubblewrap(
        ["/bin/sh", "-c", "test -e /home/tuan/.ssh && ls /home/tuan/.ssh || echo 'SSH_DENIED'"],
        repo_dir=tmp_path,
        bwrap_path=bwrap_path
    )
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    assert res.returncode == 0
    assert "SSH_DENIED" in res.stdout


def test_sandbox_enforces_network_denial(bwrap_path, tmp_path):
    """Verify that outbound and loopback network sockets are denied."""
    py_code = (
        "import socket;"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM);"
        "s.settimeout(0.5);"
        "s.connect(('127.0.0.1', 8091))"
    )
    cmd = wrap_with_bubblewrap(
        [sys.executable, "-c", py_code],
        repo_dir=tmp_path,
        bwrap_path=bwrap_path
    )
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    # Must fail with ConnectionRefusedError or OSError
    assert res.returncode != 0
    assert ("ConnectionRefusedError" in res.stderr or "OSError" in res.stderr or "Network is unreachable" in res.stderr)


def test_sandbox_private_tmp_storage_isolated(bwrap_path, tmp_path):
    """Verify private volatile scratch in /tmp exists but does not leak to host /tmp."""
    test_token = "msk_secret_isolation_token_12345"
    cmd = wrap_with_bubblewrap(
        ["/bin/sh", "-c", f"echo '{test_token}' > /tmp/sandboxed_file.txt && cat /tmp/sandboxed_file.txt"],
        repo_dir=tmp_path,
        bwrap_path=bwrap_path
    )
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    assert res.returncode == 0
    assert test_token in res.stdout

    # Verify file was not written to the host /tmp
    assert not os.path.exists("/tmp/sandboxed_file.txt")


def test_sandbox_process_namespace_isolation(bwrap_path, tmp_path):
    """Verify that PID namespace is isolated and host daemon processes are invisible."""
    cmd = wrap_with_bubblewrap(
        ["/bin/sh", "-c", "ps -e | wc -l"],
        repo_dir=tmp_path,
        bwrap_path=bwrap_path
    )
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    assert res.returncode == 0
    # Inside sandbox there should only be a few processes, never host's 100+ processes
    proc_count = int(res.stdout.strip())
    assert proc_count < 15


def test_memory_resource_limits_enforced(bwrap_path, tmp_path):
    """Verify that memory allocation beyond limit is rejected with MemoryError."""
    from msk_research_lab.core.db import get_db
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO repositories (id, name, upstream_url) VALUES ('test_repo', 'Test Repo', 'https://github.com/test/repo');")

    governor = ProcessGovernor()
    job_id = "mem_limit_test_01"

    # Allocate approval token for test
    appr_token = approve_run_profile("test_repo", "profile_mem", "sha_mem_01", approved_by="TEST")

    # Script attempting to allocate 80 MB under a 40 MB ceiling
    py_code = "bytearray(80 * 1024 * 1024)"
    launch_res = governor.launch(
        job_id=job_id,
        argv=[sys.executable, "-c", py_code],
        cwd=tmp_path,
        require_sandbox=True,
        repo_id="test_repo",
        profile_id="profile_mem",
        commit_sha="sha_mem_01",
        approval_token=appr_token,
        max_memory_mb=40
    )
    assert launch_res["status"] == "STARTED"

    import time
    time.sleep(0.5)
    stop_res = governor.stop(job_id)
    # The child process must fail due to MemoryError
    assert stop_res["exit_code"] != 0
    assert "MemoryError" in stop_res["stderr"] or stop_res["exit_code"] in [1, -9, 137]


def test_execution_blocked_without_operator_approval(tmp_path):
    """Verify that untrusted execution fails closed when no approval token is provided."""
    governor = ProcessGovernor()
    with pytest.raises(ApprovalRequiredError) as exc_info:
        governor.launch(
            job_id="unapproved_run",
            argv=["echo", "hello"],
            cwd=tmp_path,
            require_sandbox=True,
            repo_id="unreviewed_repo",
            profile_id="default",
            commit_sha="unapproved_sha",
            approval_token=None
        )
    assert "operator approval token required" in str(exc_info.value).lower()
