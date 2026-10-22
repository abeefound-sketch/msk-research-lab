"""Security and negative tests for R0 (SEC-01..SEC-05)."""

from fastapi.testclient import TestClient
from msk_research_lab.api.app import app
from msk_research_lab.__main__ import is_port_in_use

client = TestClient(app)


def test_sec_reject_non_loopback_host():
    """SEC: Non-loopback Host header must be rejected with 403 Forbidden."""
    response = client.get("/api/v1/health", headers={"host": "malicious-domain.com"})
    assert response.status_code == 403
    assert "Forbidden" in response.text


def test_sec_cors_disallows_wildcard():
    """SEC: CORS origin must not allow arbitrary third-party origins."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://evil-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    # The Access-Control-Allow-Origin header must either not be set or not match evil-site.com
    allowed_origin = response.headers.get("access-control-allow-origin")
    assert allowed_origin != "http://evil-site.com"
    assert allowed_origin != "*"


def test_sec_port_checker():
    """SEC: Verify port in-use detection logic."""
    # A port not in use should return False
    assert is_port_in_use(59999) is False
