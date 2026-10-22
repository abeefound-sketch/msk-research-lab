"""Sandbox and container isolation probe for WSL2 host environment."""

import shutil
import subprocess
from typing import Dict, Any


def probe_sandbox_capabilities() -> Dict[str, Any]:
    """Inspect whether enforceable rootless container isolation is available on this host.

    Never claim sandbox availability from configuration files alone.
    """
    podman_path = shutil.which("podman")
    docker_path = shutil.which("docker")

    runtime = None
    if podman_path:
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
            "details": "Neither Podman nor Docker runtime detected on this WSL2 host. Native subprocess execution of untrusted upstream code is strictly prohibited by security policy.",
            "checks": {
                "container_binary": False,
                "mount_isolation": False,
                "network_denial": False,
                "cgroup_memory_limit": False
            }
        }

    cmd_name, cmd_path = runtime
    # Probe runtime version
    try:
        res = subprocess.run([cmd_path, "--version"], capture_output=True, text=True, timeout=5)
        version_str = res.stdout.strip()
    except Exception as e:
        version_str = str(e)

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
            "cgroup_memory_limit": False
        }
    }
