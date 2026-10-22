"""Integration tests for GET /api/v1/health endpoint."""

from fastapi.testclient import TestClient
from msk_research_lab.api.app import app

client = TestClient(app)


def test_get_health_ok():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["app"] == "MSK Research Lab OS"
    assert data["version"] == "3.0.0"
    assert data["release"] == "R0"
    assert data["target_display"] == "1366x768"
    assert "uptime_seconds" in data
    assert "process_rss_mb" in data

    # Database integrity
    db = data["database"]
    assert db["connected"] is True
    assert db["wal_mode"] is True
    assert db["fk_enabled"] is True
    assert db["schema_version"] >= 1

    # Sandbox truth
    sb = data["sandbox"]
    assert "status" in sb
    assert sb["status"] == "SANDBOX_UNAVAILABLE"

    # Ports
    ports = data["ports"]
    assert ports["dashboard_port"] == 8091
    assert ports["loopback_only"] is True
