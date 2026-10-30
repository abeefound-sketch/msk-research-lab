"""P11 Security & Durability Verification Test Suite.

Validates:
1. DEF-27: Atomic database replacement during backup restoration.
2. DEF-29: Comprehensive clinical free-text PHI scrubber and Safe Harbor export flags.
3. DEF-30: Uniform measurement provenance categorization.
4. DEF-31: Resilient Windows security descriptor execution identity fallback.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from msk_research_lab.scientific.provenance import (
    MeasurementProvenanceType,
    build_measurement_provenance,
)
from msk_research_lab.security.key_lifecycle import (
    create_encrypted_backup,
    restore_encrypted_backup,
    rotate_pepper,
)
from msk_research_lab.security.permissions import (
    get_current_windows_identity,
    secure_directory_permissions,
    secure_file_permissions,
)
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    export_deidentified_research_record,
    scrub_phi_from_text,
)


def test_def27_atomic_restore_preserves_integrity(tmp_path):
    """Verify DEF-27: Backup restore writes to temporary files before atomic replacement."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    restore_target = tmp_path / "restored_db"
    restore_target.mkdir(parents=True, exist_ok=True)

    # Create backup archive
    pwd = "AuditPassword#P11Restore2026!"
    archive_path = create_encrypted_backup(password=pwd, target_export_dir=backup_dir)
    assert archive_path.exists()

    # Restore to directory
    res = restore_encrypted_backup(encrypted_backup_path=archive_path, password=pwd, target_restore_dir=restore_target)
    assert res["status"] == "RESTORED"
    assert (restore_target / "lab.sqlite3").exists()

    # Verify no dangling temporary files left in directory
    tmp_files = list(restore_target.glob(".*.tmp.*"))
    assert len(tmp_files) == 0


def test_def29_enhanced_phi_scrubbing_textual_dates_mrn_ip_zip():
    """Verify DEF-29: Scrubbing of textual dates, MRNs, IP addresses, and postal codes."""
    note = (
        "Patient seen on October 14, 2024 by Dr. Alexander Smith. "
        "Referred on 12 Jan 2023. MRN: 98765432. "
        "Workstation accessed from 192.168.1.105. "
        "Billing address ZIP: 90210-4321. "
        "Patient email: alex@example.org, SSN: 123-45-6789."
    )
    scrubbed = scrub_phi_from_text(note)

    # Direct checks
    assert "October 14, 2024" not in scrubbed
    assert "12 Jan 2023" not in scrubbed
    assert "98765432" not in scrubbed
    assert "192.168.1.105" not in scrubbed
    assert "90210-4321" not in scrubbed
    assert "alex@example.org" not in scrubbed
    assert "123-45-6789" not in scrubbed
    assert "Dr. Alexander Smith" not in scrubbed

    # Tokens present
    assert "[REDACTED_DATE]" in scrubbed
    assert "[REDACTED_MRN]" in scrubbed
    assert "[REDACTED_IP]" in scrubbed
    assert "[REDACTED_POSTAL_CODE]" in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "[REDACTED_SSN]" in scrubbed
    assert "[REDACTED_PROVIDER]" in scrubbed


def test_def29_safe_harbor_export_metadata_flags():
    """Verify DEF-29: Export contains explicit regex limitation and non-anonymized disclosures."""
    pat = create_patient(
        full_name="Test Subject P11",
        primary_complaint="Seen on Nov 15 2023 with MRN: 12345",
        age=45,
        gender="O",
        medical_history="IP connection logged 10.0.0.1 and ZIP: 10001",
    )

    record = export_deidentified_research_record(pat["id"])

    assert record["regex_based_scrubbing_only"] is True
    assert record["not_anonymized_guaranteed"] is True
    assert record["pii_redacted"] is True
    assert record["hipaa_safe_harbor_certified"] is False
    assert "[REDACTED_DATE]" in record["primary_complaint"]
    assert "[REDACTED_MRN]" in record["primary_complaint"]
    assert "[REDACTED_IP]" in record["medical_history_summary"]
    assert "[REDACTED_POSTAL_CODE]" in record["medical_history_summary"]


def test_def30_uniform_measurement_provenance_types():
    """Verify DEF-30: Uniform classification of measurement provenance."""
    # 1. LIVE_MEASURED
    live = build_measurement_provenance(MeasurementProvenanceType.LIVE_MEASURED, source="STEREO_CAMERA_RIG")
    assert live["provenance_type"] == "LIVE_MEASURED"
    assert live["is_live_measurement"] is True
    assert live["is_synthetic"] is False
    assert live["is_valid"] is True
    assert live["clinical_use_permitted"] is False

    # 2. SYNTHETIC_TEST
    synth = build_measurement_provenance(MeasurementProvenanceType.SYNTHETIC_TEST, source="FIXTURE_ELBOW")
    assert synth["provenance_type"] == "SYNTHETIC_TEST"
    assert synth["is_live_measurement"] is False
    assert synth["is_synthetic"] is True
    assert synth["is_valid"] is True

    # 3. NOT_MEASURABLE
    unmeas = build_measurement_provenance(MeasurementProvenanceType.NOT_MEASURABLE, details={"reason": "OCCLUSION"})
    assert unmeas["provenance_type"] == "NOT_MEASURABLE"
    assert unmeas["is_valid"] is False

    # 4. INVALID_INPUT
    inv = build_measurement_provenance(MeasurementProvenanceType.INVALID_INPUT, details={"error": "SINGULAR_MATRIX"})
    assert inv["provenance_type"] == "INVALID_INPUT"
    assert inv["is_valid"] is False


def test_def31_windows_identity_resolution_fallback(monkeypatch):
    """Verify DEF-31: Windows identity resolution succeeds even when USERNAME and USER env are unset."""
    # Clear env vars
    monkeypatch.delenv("USERNAME", raising=False)
    monkeypatch.delenv("USER", raising=False)

    identity = get_current_windows_identity()
    assert identity is not None
    assert len(identity) > 0
    # Should resolve to either the local username via getpass or the standard SID fallback
    assert identity != ""
