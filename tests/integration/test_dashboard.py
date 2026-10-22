"""Integration tests for web dashboard rendering and responsiveness."""

from fastapi.testclient import TestClient
from msk_research_lab.api.app import app

client = TestClient(app)


def test_dashboard_renders_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text

    # Viewport for 1366x768 and responsive displays
    assert 'name="viewport"' in html
    assert 'content="width=device-width, initial-scale=1.0"' in html

    # Core dashboard sections
    assert "MSK Research Lab OS" in html
    assert "R0 Verified" in html
    assert "System Health" in html
    assert "SQLite" in html
    assert "Sandbox Isolation" in html
    assert "SANDBOX_UNAVAILABLE" in html
    assert "Candidate Repositories" in html
    assert "LOCAL 127.0.0.1:8091" in html


def test_dashboard_alias_route():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
