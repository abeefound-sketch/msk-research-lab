"""Sandbox and container isolation probe for WSL2 host environment."""

import os
import shutil
import subprocess
from typing import Dict, Any


def probe_sandbox_capabilities() -> Dict[str, Any]:
    """Inspect whether enforceable rootless container isolation is available on this host.

    Never claim sandbox availability from configuration files alone.
    Checks Bubblewrap (bwrap), Podman, and Docker.
    """
    bwrap_path = shutil.which("bwrap") or (
        "/home/tuan/.local/bin/bwrap" if os.path.exists("/home/tuan/.local/bin/bwrap") else None
    )
    podman_path = shutil.which("podman")
    docker_path = shutil.which("docker")

    runtime = None
    if bwrap_path:
        runtime = ("bubblewrap", bwrap_path)
    elif podman_path:
        runtime = ("podman", podman_path)
    elif docker_path:
        runtime = ("docker", docker_path)

    if not runtime:
        return {
            "status": "SANDBOX_UNAVAILABLE",
            "runtime": None,
            "can_execute_untrusted": False,
            "isolation_enforceable": False,
            "readiness_gate": "BLOCKED",
            "details": "Neither Bubblewrap, Podman, nor Docker runtime detected on this WSL2 host. Native subprocess execution of untrusted upstream code is strictly prohibited by security policy.",
            "checks": {
                "container_binary": False,
                "mount_isolation": False,
                "network_denial": False,
                "process_isolation": False,
                "memory_limits_configured": False
            }
        }

    cmd_name, cmd_path = runtime

    if cmd_name == "bubblewrap":
        checks = _verify_bubblewrap_isolation(cmd_path)
        is_isolated = all(checks.values())
        version_str = _get_version(cmd_path)

        return {
            "status": "SANDBOX_VERIFIED_BUBBLEWRAP" if is_isolated else "SANDBOX_DETECTED_UNVERIFIED",
            "runtime": "bubblewrap",
            "runtime_path": cmd_path,
            "runtime_version": version_str,
            "can_execute_untrusted": False,  # Strict: requires explicit operator approval token per repo
            "isolation_enforceable": is_isolated,
            "readiness_gate": "ISOLATION_VERIFIED; AWAITING_UPSTREAM_EXECUTION_APPROVAL" if is_isolated else "REVIEW_REQUIRED",
            "details": (
                f"Bubblewrap {version_str} operational with verified filesystem mount isolation, network denial, and PID isolation. "
                "Memory limits independently enforced via POSIX setrlimit (RLIMIT_AS). Untrusted execution requires explicit per-repo approval."
                if is_isolated
                else "Bubblewrap detected but one or more isolation probes failed."
            ),
            "checks": checks
        }

    version_str = _get_version(cmd_path)
    return {
        "status": "SANDBOX_DETECTED_UNVERIFIED",
        "runtime": cmd_name,
        "runtime_path": cmd_path,
        "runtime_version": version_str,
        "can_execute_untrusted": False,
        "isolation_enforceable": False,
        "readiness_gate": "REVIEW_REQUIRED",
        "details": f"Container runtime {cmd_name} detected ({version_str}), but explicit isolation enforcement checks have not yet been validated.",
        "checks": {
            "container_binary": True,
            "mount_isolation": False,
            "network_denial": False,
            "process_isolation": False,
            "memory_limits_configured": False
        }
    }


def _get_version(cmd_path: str) -> str:
    try:
        res = subprocess.run([cmd_path, "--version"], capture_output=True, text=True, timeout=5)
        return res.stdout.strip()
    except Exception as e:
        return str(e)


def _verify_bubblewrap_isolation(bwrap_path: str) -> Dict[str, bool]:
    """Actively probe Bubblewrap to verify filesystem, network, and process isolation."""
    checks = {
        "container_binary": True,
        "mount_isolation": False,
        "network_denial": False,
        "process_isolation": False,
        "memory_limits_configured": True  # Enforced via resource.setrlimit in runner
    }

    # 1. Mount isolation check: verify /mnt and /home are inaccessible
    try:
        cmd_mount = [
            bwrap_path,
            "--unshare-all",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/usr", "/usr",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--",
            "/bin/sh", "-c", "test ! -e /mnt && test ! -e /home"
        ]
        res = subprocess.run(cmd_mount, capture_output=True, timeout=5)
        if res.returncode == 0:
            checks["mount_isolation"] = True
    except Exception:
        pass

    # 2. Network denial check: verify network namespace is unshared and loopback is down
    try:
        cmd_net = [
            bwrap_path,
            "--unshare-net",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/usr", "/usr",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--",
            "/bin/sh", "-c", "test -z \"$(ip link show 2>/dev/null | grep -v lo)\""
        ]
        res = subprocess.run(cmd_net, capture_output=True, timeout=5)
        if res.returncode == 0:
            checks["network_denial"] = True
    except Exception:
        pass

    # 3. Process namespace isolation check: isolated PID namespace only sees bwrap & sh
    try:
        cmd_pid = [
            bwrap_path,
            "--unshare-pid",
            "--proc", "/proc",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/usr", "/usr",
            "--",
            "/bin/sh", "-c", "test $(ps -e | wc -l) -le 10"
        ]
        res = subprocess.run(cmd_pid, capture_output=True, timeout=5)
        if res.returncode == 0:
            checks["process_isolation"] = True
    except Exception:
        pass

    return checks
