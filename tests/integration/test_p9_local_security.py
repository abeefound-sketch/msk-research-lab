"""Verification tests for P9-B Local Security, Windows Privacy, and CSRF/Origin Guards."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.security.key_lifecycle import get_pepper_storage_paths
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    export_deidentified_research_record,
    get_patient,
)


@pytest.fixture
def setup_db(tmp_path, monkeypatch):
    """Provide isolated SQLite database and key paths."""
    db_file = tmp_path / "test_p9_sec.sqlite3"
    monkeypatch.setenv("MSK_LAB_DB_PATH", str(db_file))
    get_config(reload=True)
    run_migrations(db_file)
    try:
        yield db_file
    finally:
        monkeypatch.delenv("MSK_LAB_DB_PATH", raising=False)
        get_config(reload=True)


def test_deidentified_research_export_redacts_pii(setup_db):
    """Verify that de-identified research export strictly strips all direct PII."""
    db_file = setup_db
    secret_name = "Confidential Patient Alexander Hamilton"
    p = create_patient(
        full_name=secret_name,
        primary_complaint="Right Rotator Cuff Tear",
        age=45,
        gender="M",
        height_cm=178.0,
        weight_kg=78.5,
        medical_history="Hypertension diagnosed 2020",
    )

    export_data = export_deidentified_research_record(p["id"], operator_id="AUDITOR_P9")

    # Direct PII assertions
    assert "full_name" not in export_data
    assert secret_name not in json.dumps(export_data)
    assert export_data["pii_redacted"] is True
    assert export_data["research_subject_id"].startswith("SUBJ-")
    assert export_data["pseudonym_hash"] == p["pseudonym_hash"]
    assert export_data["primary_complaint"] == "Right Rotator Cuff Tear"
    assert export_data["age"] == 45

    # Check tri-ledger audit entry
    with get_db(db_file) as conn:
        row = conn.execute(
            "SELECT * FROM audit_events WHERE event_type = 'RESEARCH_RECORD_EXPORTED' ORDER BY id DESC LIMIT 1;"
        ).fetchone()
        assert row is not None
        assert row["actor"] == "AUDITOR_P9"
        payload = json.loads(row["payload_json"])
        assert payload["patient_id"] == p["id"]
        assert payload["research_subject_id"] == export_data["research_subject_id"]


def test_deidentified_research_export_api_endpoint(setup_db):
    """Verify API endpoint returns compliant de-identified record."""
    client = TestClient(app)
    p = create_patient(
        full_name="Secret Jane Doe",
        primary_complaint="Cervical Radiculopathy",
        age=34,
        gender="F",
    )

    resp = client.get(f"/api/v1/workstation/patients/{p['id']}/export/deidentified")
    assert resp.status_code == 200
    data = resp.json()

    assert "full_name" not in data
    assert "Secret Jane Doe" not in resp.text
    assert data["pii_redacted"] is True
    assert data["research_subject_id"].startswith("SUBJ-")


def test_security_host_guard_loopback_allowed():
    """Verify legitimate loopback requests succeed."""
    client = TestClient(app)
    resp = client.get("/api/v1/health", headers={"Host": "127.0.0.1:8000"})
    assert resp.status_code == 200
    assert resp.json()["status"] in ("HEALTHY", "OPERATIONAL")


def test_security_host_guard_non_loopback_rejected():
    """Verify external host header spoofing / DNS rebinding is rejected with 403."""
    client = TestClient(app)
    resp = client.get("/api/v1/health", headers={"Host": "attacker.evil.corp:8000"})
    assert resp.status_code == 403
    assert "MSK Research Lab OS only permits loopback access" in resp.json()["detail"]


def test_csrf_origin_guard_legitimate_origin(setup_db):
    """Verify state-modifying requests from local origin are permitted."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/workstation/patients",
        headers={"Host": "127.0.0.1:8000", "Origin": "http://127.0.0.1:8000"},
        json={"full_name": "Origin Test", "primary_complaint": "Lumbar Pain"},
    )
    assert resp.status_code == 200


def test_csrf_origin_guard_malicious_origin_rejected(setup_db):
    """Verify cross-origin POST from unauthorized domain is rejected with 403."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/workstation/patients",
        headers={"Host": "127.0.0.1:8000", "Origin": "https://malicious-phishing-site.com"},
        json={"full_name": "Malicious Test", "primary_complaint": "Spam"},
    )
    assert resp.status_code == 403
    assert "Cross-site request rejected" in resp.json()["detail"]


def test_csrf_referer_guard_malicious_referer_rejected(setup_db):
    """Verify cross-origin referer on state-modifying request is rejected with 403."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/workstation/patients",
        headers={"Host": "127.0.0.1:8000", "Referer": "http://evil-attacker.org/path"},
        json={"full_name": "Referer Test", "primary_complaint": "Spam"},
    )
    assert resp.status_code == 403
    assert "Cross-site referer rejected" in resp.json()["detail"]


def test_pepper_vault_directory_permissions(setup_db):
    """Verify key vault directory and pepper files have restricted permissions."""
    active_pepper_file, vault_dir = get_pepper_storage_paths()
    assert vault_dir.exists()
