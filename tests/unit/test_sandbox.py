"""Unit tests for sandbox isolation probe and security gates."""

from msk_research_lab.sandbox.probe import probe_sandbox_capabilities


def test_sandbox_probe_honesty():
    """Verify that sandbox detection truthfully reflects the machine state without false PASS."""
    probe = probe_sandbox_capabilities()
    assert "status" in probe
    assert "can_execute_untrusted" in probe
    assert "readiness_gate" in probe

    # On this WSL host without Podman or Docker, it must report SANDBOX_UNAVAILABLE and BLOCKED
    if probe["runtime"] is None:
        assert probe["status"] == "SANDBOX_UNAVAILABLE"
        assert probe["can_execute_untrusted"] is False
        assert probe["readiness_gate"] == "BLOCKED"
        assert "Neither Podman nor Docker" in probe["details"]
    else:
        # If a container runtime is present, isolation must not be claimed blindly
        assert probe["can_execute_untrusted"] is False
