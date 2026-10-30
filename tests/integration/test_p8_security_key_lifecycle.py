"""Tests for P8-B Cryptographic Key Lifecycle, Pepper Rotation, and Encrypted Recovery."""

import os
import secrets
from pathlib import Path
import pytest
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.security.key_lifecycle import (
    BackupDecryptionError,
    create_encrypted_backup,
    get_current_pepper_version,
    restore_encrypted_backup,
    rotate_pepper,
)
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    get_patient,
    get_pseudonym_hash,
)


@pytest.fixture
def setup_db(tmp_path, monkeypatch):
    """Provide isolated SQLite database and key paths for key lifecycle tests."""
    db_file = tmp_path / "test_lab.sqlite3"
    monkeypatch.setenv("MSK_LAB_DB_PATH", str(db_file))
    get_config(reload=True)
    run_migrations(db_file)
    try:
        yield db_file
    finally:
        monkeypatch.delenv("MSK_LAB_DB_PATH", raising=False)
        get_config(reload=True)


def test_pepper_migration_and_patient_pepper_version(setup_db):
    """Verify migration 10 populated pepper_version and tables correctly."""
    db_file = setup_db
    p = create_patient(full_name="Key Lifecycle Test Patient", primary_complaint="Lumbar ache")
    assert p["pepper_version"] == 1
    assert len(p["pseudonym_hash"]) == 64

    with get_db(db_file) as conn:
        res = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pepper_rotation_log';").fetchone()
        assert res is not None


def test_rotate_pepper_zero_record_loss(setup_db):
    """Verify rotate_pepper re-keys all patient records with journal audit and zero record loss."""
    db_file = setup_db

    # Register 3 patients
    p1 = create_patient(full_name="Patient One", primary_complaint="Knee instability")
    p2 = create_patient(full_name="Patient Two", primary_complaint="Cervical radiculopathy")
    p3 = create_patient(full_name="Patient Three", primary_complaint="Shoulder impingement")

    old_hash1 = p1["pseudonym_hash"]
    old_hash2 = p2["pseudonym_hash"]

    # Rotate pepper
    new_pepper_bytes = secrets.token_bytes(32)
    res = rotate_pepper(new_pepper=new_pepper_bytes, operator_id="AUDITOR_01", custom_path=db_file)

    assert res["status"] == "SUCCESS"
    assert res["from_version"] == 1
    assert res["to_version"] == 2
    assert res["records_migrated"] >= 3

    # Check updated records
    up_p1 = get_patient(p1["id"])
    up_p2 = get_patient(p2["id"])

    assert up_p1["pepper_version"] == 2
    assert up_p2["pepper_version"] == 2
    assert up_p1["pseudonym_hash"] != old_hash1
    assert up_p1["pseudonym_hash"] == get_pseudonym_hash(p1["id"], pepper=new_pepper_bytes)

    # Check pepper_rotation_log entry
    with get_db(db_file) as conn:
        row = conn.execute("SELECT * FROM pepper_rotation_log ORDER BY id DESC LIMIT 1;").fetchone()
        assert row["from_version"] == 1
        assert row["to_version"] == 2
        assert row["records_migrated"] >= 3
        assert row["status"] == "COMPLETED"


def test_encrypted_backup_and_restore(setup_db, tmp_path):
    """Verify creating and restoring an authenticated encrypted backup archive."""
    db_file = setup_db
    p = create_patient(full_name="Encrypted Backup Subject", primary_complaint="Acute wry neck")

    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restored"

    password = "CorrectHorseBatteryStaple2026!"
    backup_file = create_encrypted_backup(password=password, target_export_dir=backup_dir)

    assert backup_file.exists()
    assert backup_file.stat().st_size > 512

    # Verify header magic
    assert backup_file.read_bytes()[:8] in (b"MSKENC01", b"MSKENC02")

    # Restore with correct password
    res = restore_encrypted_backup(backup_file, password=password, target_restore_dir=restore_dir)
    assert res["status"] == "RESTORED"
    assert res["db_verified"] is True
    assert "lab.sqlite3" in res["files_restored"]

    # Verify patient exists in restored db
    restored_db_path = restore_dir / "lab.sqlite3"
    with get_db(restored_db_path) as conn:
        row = conn.execute("SELECT full_name FROM patients WHERE id = ?;", (p["id"],)).fetchone()
        assert row is not None
        assert row["full_name"] == "Encrypted Backup Subject"


def test_encrypted_backup_fails_on_wrong_password(setup_db, tmp_path):
    """Verify authenticated decryption raises BackupDecryptionError on incorrect password."""
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restored"

    backup_file = create_encrypted_backup(password="ValidPassword123!", target_export_dir=backup_dir)

    with pytest.raises(BackupDecryptionError) as exc_info:
        restore_encrypted_backup(backup_file, password="WrongPassword456!", target_restore_dir=restore_dir)

    assert "Authentication failed" in str(exc_info.value)
