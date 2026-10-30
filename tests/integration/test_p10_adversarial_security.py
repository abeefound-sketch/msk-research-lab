"""P10-A Adversarial Cryptography, Safe Harbor PHI Scrubbing, and Host/Origin Security Tests."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.core.config import get_config
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.security.openssl_gcm import probe_fips_status
from msk_research_lab.security.permissions import secure_directory_permissions, secure_file_permissions
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    export_deidentified_research_record,
    scrub_phi_from_text,
)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Provide isolated SQLite database for P10 security tests."""
    db_file = tmp_path / "test_p10_sec.sqlite3"
    monkeypatch.setenv("MSK_LAB_DB_PATH", str(db_file))
    get_config(reload=True)
    run_migrations(db_file)
    try:
        yield db_file
    finally:
        monkeypatch.delenv("MSK_LAB_DB_PATH", raising=False)
        get_config(reload=True)


def test_openssl_fips_status_probe_reporting():
    """Verify probe_fips_status accurately discloses provider and avoids false FIPS claim (DEF-20)."""
    status = probe_fips_status()
    assert isinstance(status, dict)
    assert status["openssl_available"] is True
    assert status["standard"] == "NIST_SP_800_38D"
    # In standard system environments without CMVP hardware tokens, is_fips must be False
    assert status["is_fips"] is False
    assert status["provider"] == "default"
    assert status["compliance_claim"] == "NIST_SP_800_38D_ALIGNED_DEFAULT_PROVIDER"


def test_phi_free_text_scrubber():
    """Verify scrub_phi_from_text strips phone, email, SSN, provider names, and dates (DEF-21)."""
    raw_text = (
        "Patient referred by Dr. Gregory House (email: house@diagnostics.org, phone: (555) 019-2834) "
        "on 04/15/2023. SSN 123-45-6789. Previous consult with Doctor Lisa Cuddy on 2022-11-30."
    )
    scrubbed = scrub_phi_from_text(raw_text)

    assert "Dr. Gregory House" not in scrubbed
    assert "Doctor Lisa Cuddy" not in scrubbed
    assert "house@diagnostics.org" not in scrubbed
    assert "(555) 019-2834" not in scrubbed
    assert "123-45-6789" not in scrubbed
    assert "04/15/2023" not in scrubbed
    assert "2022-11-30" not in scrubbed

    assert "[REDACTED_PROVIDER]" in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "[REDACTED_SSN]" in scrubbed
    assert "[REDACTED_DATE]" in scrubbed


def test_hipaa_safe_harbor_age_aggregation(isolated_db):
    """Verify Safe Harbor age aggregation: age > 89 is exported as '90+' (DEF-21)."""
    p = create_patient(
        full_name="Elderly Research Subject",
        primary_complaint="Lumbar stenosis",
        age=94,
        gender="F",
        height_cm=160.0,
        weight_kg=55.0,
    )

    export_data = export_deidentified_research_record(p["id"], operator_id="AUDITOR_P10")
    assert export_data["age"] == "90+"
    assert export_data["hipaa_safe_harbor_certified"] is False
    assert export_data["deidentification_method"] == "SYNTHETIC_RESEARCH_SCRUBBED_NOT_CERTIFIED_FOR_PHI"
    assert "NOT CERTIFIED FOR REAL PHI" in export_data["compliance_disclaimer"]


def test_hipaa_free_text_notes_scrubbing_in_export(isolated_db):
    """Verify free-text medical history, primary complaint, and red flags are scrubbed (DEF-21)."""
    p = create_patient(
        full_name="Confidential Subject",
        primary_complaint="Severe shoulder pain following consult with Dr. John Watson on 12/01/2023",
        age=52,
        gender="M",
        medical_history="Contact clinic at info@msk-clinic.com or 555-882-9910. Patient SSN: 987-65-4321.",
        red_flags={
            "fever": False,
            "referral_notes": "Urgent referral from Dr. James Wilson on 2024-01-10",
        },
    )

    export_data = export_deidentified_research_record(p["id"], operator_id="AUDITOR_P10")

    # Primary complaint scrubbed
    assert "Dr. John Watson" not in export_data["primary_complaint"]
    assert "12/01/2023" not in export_data["primary_complaint"]
    assert "[REDACTED_PROVIDER]" in export_data["primary_complaint"]
    assert "[REDACTED_DATE]" in export_data["primary_complaint"]

    # Medical history scrubbed
    assert "info@msk-clinic.com" not in export_data["medical_history_summary"]
    assert "555-882-9910" not in export_data["medical_history_summary"]
    assert "987-65-4321" not in export_data["medical_history_summary"]

    # Red flags scrubbed
    assert "Dr. James Wilson" not in export_data["red_flags"]["referral_notes"]
    assert "2024-01-10" not in export_data["red_flags"]["referral_notes"]
    assert "[REDACTED_PROVIDER]" in export_data["red_flags"]["referral_notes"]


def test_windows_and_posix_permissions_helpers(tmp_path):
    """Verify permissions helper applies restrictive DACLs / POSIX modes (DEF-22)."""
    test_file = tmp_path / "secret.key"
    test_file.write_bytes(b"very_secret_key_material")
    test_dir = tmp_path / "key_vault"
    test_dir.mkdir()

    secure_file_permissions(test_file)
    secure_directory_permissions(test_dir)

    import sys
    if sys.platform != "win32":
        # On POSIX verify 0600 and 0700 modes
        assert (test_file.stat().st_mode & 0o777) == 0o600
        assert (test_dir.stat().st_mode & 0o777) == 0o700


def test_security_host_guard_ipv6_loopback():
    """Verify IPv6 loopback [::1] and [::1]:port are allowed through security_host_guard (DEF-26)."""
    client = TestClient(app)
    resp1 = client.get("/api/v1/health", headers={"Host": "[::1]:8000"})
    assert resp1.status_code == 200

    resp2 = client.get("/api/v1/health", headers={"Host": "[::1]"})
    assert resp2.status_code == 200


def test_security_host_guard_csrf_null_origin_rejection(isolated_db):
    """Verify CSRF guard rejects state-changing requests with 'Origin: null' or external origin (DEF-16, DEF-26)."""
    client = TestClient(app)
    payload = {
        "full_name": "Attack Subject",
        "primary_complaint": "Exploit attempt",
        "age": 30,
        "gender": "M",
    }

    # 1. Null Origin (sandboxed iframe / local file exploit)
    resp_null = client.post(
        "/api/v1/workstation/patients",
        json=payload,
        headers={"Host": "127.0.0.1:8000", "Origin": "null"},
    )
    assert resp_null.status_code == 403
    assert "CSRF" in resp_null.json()["detail"] or "Forbidden" in resp_null.json()["detail"]

    # 2. Malicious External Origin
    resp_ext = client.post(
        "/api/v1/workstation/patients",
        json=payload,
        headers={"Host": "127.0.0.1:8000", "Origin": "http://malicious-site.com"},
    )
    assert resp_ext.status_code == 403

    # 3. Legitimate Loopback IPv6 Origin
    resp_ok = client.post(
        "/api/v1/workstation/patients",
        json=payload,
        headers={"Host": "[::1]:8000", "Origin": "http://[::1]:8000"},
    )
    assert resp_ok.status_code in (200, 201)
