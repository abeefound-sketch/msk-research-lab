"""Fault injection and security verification tests for P9-A Cryptography and Backup Recovery."""

import io
import os
import secrets
import sqlite3
import tarfile
from pathlib import Path
import pytest

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.security.key_lifecycle import (
    ENC_MAGIC_V1,
    ENC_MAGIC_V2,
    BackupDecryptionError,
    create_encrypted_backup,
    get_current_pepper_version,
    get_pepper_storage_paths,
    recover_active_pepper_from_vault,
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
    """Provide isolated SQLite database and key paths."""
    db_file = tmp_path / "test_p9_lab.sqlite3"
    monkeypatch.setenv("MSK_LAB_DB_PATH", str(db_file))
    get_config(reload=True)
    run_migrations(db_file)
    try:
        yield db_file
    finally:
        monkeypatch.delenv("MSK_LAB_DB_PATH", raising=False)
        get_config(reload=True)


def test_mskenc02_roundtrip_aes_gcm(setup_db, tmp_path):
    """Verify MSKENC02 container creation and restoration using OpenSSL AES-256-GCM."""
    db_file = setup_db
    p = create_patient(full_name="GCM Patient", primary_complaint="Lumbar Disc Herniation")

    backup_dir = tmp_path / "backups_v2"
    restore_dir = tmp_path / "restored_v2"
    password = "MasterKeyP9_AES_GCM_2026!"

    backup_file = create_encrypted_backup(
        password=password,
        target_export_dir=backup_dir,
        format_version="v2",
    )

    assert backup_file.exists()
    content = backup_file.read_bytes()
    # Check Magic header
    assert content[:8] == ENC_MAGIC_V2

    res = restore_encrypted_backup(backup_file, password=password, target_restore_dir=restore_dir)
    assert res["status"] == "RESTORED"
    assert res["db_verified"] is True

    # Validate restored database content
    with get_db(restore_dir / "lab.sqlite3") as conn:
        row = conn.execute("SELECT full_name FROM patients WHERE id = ?;", (p["id"],)).fetchone()
        assert row is not None
        assert row["full_name"] == "GCM Patient"


def test_mskenc01_backwards_compatibility(setup_db, tmp_path):
    """Verify legacy MSKENC01 backups are restored successfully."""
    db_file = setup_db
    p = create_patient(full_name="Legacy Patient", primary_complaint="Shoulder Impingement")

    backup_dir = tmp_path / "backups_v1"
    restore_dir = tmp_path / "restored_v1"
    password = "LegacyPassword2026!"

    backup_file = create_encrypted_backup(
        password=password,
        target_export_dir=backup_dir,
        format_version="v1",
    )

    assert backup_file.read_bytes()[:8] == ENC_MAGIC_V1

    res = restore_encrypted_backup(backup_file, password=password, target_restore_dir=restore_dir)
    assert res["status"] == "RESTORED"
    assert res["db_verified"] is True

    with get_db(restore_dir / "lab.sqlite3") as conn:
        row = conn.execute("SELECT full_name FROM patients WHERE id = ?;", (p["id"],)).fetchone()
        assert row is not None
        assert row["full_name"] == "Legacy Patient"


def test_fault_wrong_password_rejected(setup_db, tmp_path):
    """Verify wrong password raises BackupDecryptionError for both V2 and V1 containers."""
    create_patient(full_name="Auth Failure Test", primary_complaint="Cervical Sprain")
    backup_v2 = create_encrypted_backup(password="CorrectV2Password!", target_export_dir=tmp_path / "b2", format_version="v2")
    backup_v1 = create_encrypted_backup(password="CorrectV1Password!", target_export_dir=tmp_path / "b1", format_version="v1")

    # V2 wrong password
    with pytest.raises(BackupDecryptionError) as exc_v2:
        restore_encrypted_backup(backup_v2, password="IncorrectPassword!", target_restore_dir=tmp_path / "r2")
    assert "Authentication failed" in str(exc_v2.value)

    # V1 wrong password
    with pytest.raises(BackupDecryptionError) as exc_v1:
        restore_encrypted_backup(backup_v1, password="IncorrectPassword!", target_restore_dir=tmp_path / "r1")
    assert "Authentication failed" in str(exc_v1.value)


def test_fault_tampered_ciphertext_rejected(setup_db, tmp_path):
    """Verify single-bit flipping in ciphertext fails GMAC tag authentication fail-closed."""
    create_patient(full_name="Ciphertext Tamper Test", primary_complaint="Knee Meniscus Tear")
    backup_file = create_encrypted_backup(password="SecretKey123!", target_export_dir=tmp_path / "b_tamper", format_version="v2")

    raw = bytearray(backup_file.read_bytes())
    # Container V2: 8B magic + 16B salt + 12B IV + 16B tag + Ciphertext
    header_offset = 8 + 16 + 12 + 16
    assert len(raw) > header_offset + 10
    # Flip one bit in ciphertext
    raw[header_offset + 5] ^= 0x01
    tampered_file = tmp_path / "tampered.enc"
    tampered_file.write_bytes(raw)

    with pytest.raises(BackupDecryptionError) as exc:
        restore_encrypted_backup(tampered_file, password="SecretKey123!", target_restore_dir=tmp_path / "r_tamper")
    assert "Authentication failed" in str(exc.value)


def test_fault_tampered_tag_rejected(setup_db, tmp_path):
    """Verify single-bit flipping in authentication tag fails fail-closed."""
    create_patient(full_name="Tag Tamper Test", primary_complaint="Plantar Fasciitis")
    backup_file = create_encrypted_backup(password="SecretKey123!", target_export_dir=tmp_path / "b_tag", format_version="v2")

    raw = bytearray(backup_file.read_bytes())
    # Tag offset: 8B magic + 16B salt + 12B IV = 36
    tag_offset = 36
    raw[tag_offset + 2] ^= 0x80
    tampered_file = tmp_path / "tag_tampered.enc"
    tampered_file.write_bytes(raw)

    with pytest.raises(BackupDecryptionError) as exc:
        restore_encrypted_backup(tampered_file, password="SecretKey123!", target_restore_dir=tmp_path / "r_tag")
    assert "Authentication failed" in str(exc.value)


def test_fault_truncated_archive_rejected(setup_db, tmp_path):
    """Verify truncated encrypted archive raises BackupDecryptionError."""
    create_patient(full_name="Truncation Test", primary_complaint="Elbow Tendonitis")
    backup_file = create_encrypted_backup(password="SecretKey123!", target_export_dir=tmp_path / "b_trunc", format_version="v2")

    raw = backup_file.read_bytes()
    truncated_file = tmp_path / "truncated.enc"
    truncated_file.write_bytes(raw[:45])  # Cut off mid-container

    with pytest.raises(BackupDecryptionError):
        restore_encrypted_backup(truncated_file, password="SecretKey123!", target_restore_dir=tmp_path / "r_trunc")


def test_fault_corrupted_sqlite_in_archive_rejected(tmp_path):
    """Verify corrupted SQLite within decrypted tar is caught in isolated staging and does not poison target dir."""
    from msk_research_lab.security.openssl_gcm import aes_256_gcm_encrypt
    from msk_research_lab.security.key_lifecycle import _derive_key_v2

    # Create dummy tar containing a corrupted lab.sqlite3
    tar_bytes_io = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes_io, mode="w") as tar:
        corrupted_db_data = b"SQLite format 3\x00NotAValidDatabaseFileCorruptedHeaderData"
        ti = tarfile.TarInfo(name="lab.sqlite3")
        ti.size = len(corrupted_db_data)
        tar.addfile(ti, io.BytesIO(corrupted_db_data))

    tar_bytes = tar_bytes_io.getvalue()
    password = "ValidPassword123!"
    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    key = _derive_key_v2(password, salt)
    aad = ENC_MAGIC_V2 + salt + iv
    ciphertext, tag = aes_256_gcm_encrypt(key, iv, tar_bytes, aad=aad)

    corrupt_backup = tmp_path / "corrupt_db.enc"
    corrupt_backup.write_bytes(ENC_MAGIC_V2 + salt + iv + tag + ciphertext)

    target_restore_dir = tmp_path / "isolated_target"
    target_restore_dir.mkdir(parents=True, exist_ok=True)
    # Pre-populate target with valid marker to ensure it is NOT poisoned or overwritten
    marker_file = target_restore_dir / "preserve_marker.txt"
    marker_file.write_text("MUST_PRESERVE")

    with pytest.raises(BackupDecryptionError) as exc:
        restore_encrypted_backup(corrupt_backup, password=password, target_restore_dir=target_restore_dir)

    assert "Corrupted database" in str(exc.value) or "Staged database validation failed" in str(exc.value)
    # Ensure marker file is still preserved and no corrupted lab.sqlite3 leaked
    assert marker_file.exists()
    assert marker_file.read_text() == "MUST_PRESERVE"
    assert not (target_restore_dir / "lab.sqlite3").exists()


def test_two_phase_pepper_rotation_and_recovery(setup_db):
    """Verify write-ahead key rotation, key vault archiving, and automatic recovery on desync."""
    db_file = setup_db
    p = create_patient(full_name="Rotation Patient", primary_complaint="Carpal Tunnel")
    active_pepper_file, vault_dir = get_pepper_storage_paths()

    assert active_pepper_file.exists()
    v1_bytes = active_pepper_file.read_bytes()
    assert get_current_pepper_version(db_file) == 1

    # Rotate pepper
    new_pepper_bytes = secrets.token_bytes(32)
    res = rotate_pepper(new_pepper=new_pepper_bytes, operator_id="SEC_ADMIN", custom_path=db_file)
    assert res["status"] == "SUCCESS"
    assert res["to_version"] == 2

    # Check key vault has v1 and v2 archived
    v1_archive = vault_dir / "pepper_v1.key"
    v2_archive = vault_dir / "pepper_v2.key"
    assert v1_archive.exists()
    assert v2_archive.exists()
    assert v1_archive.read_bytes() == v1_bytes
    assert v2_archive.read_bytes() == new_pepper_bytes
    assert active_pepper_file.read_bytes() == new_pepper_bytes

    # Simulate disaster: active pepper file deleted
    active_pepper_file.unlink()
    assert not active_pepper_file.exists()

    # Call automatic recovery
    rec_res = recover_active_pepper_from_vault(custom_path=db_file)
    assert rec_res["status"] == "RECOVERED"
    assert rec_res["recovered_from_vault"] is True
    assert active_pepper_file.exists()
    assert active_pepper_file.read_bytes() == new_pepper_bytes
