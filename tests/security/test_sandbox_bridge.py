"""Security and functionality tests for Sandbox Web Bridge & Unix Socket Proxy."""

import time
import urllib.request
import pytest
from pathlib import Path
from msk_research_lab.sandbox.bridge import SandboxedAppRunner
from msk_research_lab.sandbox.probe import probe_sandbox_capabilities


def test_sandbox_bridge_e2e_isolation_and_serving(tmp_path):
    probe = probe_sandbox_capabilities()
    if not probe["isolation_enforceable"]:
        pytest.skip("Bubblewrap isolation not available on this host.")

    # Create dummy static app
    app_dir = tmp_path / "mock_app"
    app_dir.mkdir()
    index_html = app_dir / "index.html"
    index_html.write_text("<!DOCTYPE html><html><body><h1>Isolated 3D Sandbox</h1></body></html>", encoding="utf-8")

    runner = SandboxedAppRunner(
        repo_id="mock_app",
        repo_path=app_dir,
        port=8099,
        memory_limit_bytes=400 * 1024 * 1024
    )

    try:
        metrics = runner.start()
        assert metrics["status"] == "RUNNING"
        assert metrics["port"] == 8099
        assert metrics["pid"] is not None

        # Verify host loopback bridge responds
        url = "http://127.0.0.1:8099/index.html"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            assert response.status == 200
            content = response.read().decode("utf-8")
            assert "Isolated 3D Sandbox" in content

        # Verify memory metrics
        time.sleep(0.5)
        current_metrics = runner.get_process_metrics()
        assert current_metrics["rss_kb"] > 0
        assert current_metrics["rss_mb"] < 100.0  # RSS should be well under 100MB for python static server

    finally:
        runner.stop()
        assert runner.is_running is False
        assert runner.container_proc is None
