"""P10-B Crash-Consistent Data Durability and Disaster Recovery Fault Injection Tests."""

import io
import json
import os
from pathlib import Path
import sqlite3
import tarfile
import pytest

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import (
    MIGRATIONS,
    MigrationError,
    get_applied_migrations,
    run_migrations,
)
from msk_research_lab.security.key_lifecycle import (
    BackupDecryptionError,
    create_encrypted_backup,
    get_current_pepper_version,
    get_pepper_storage_paths,
    restore_encrypted_backup,
    rotate_pepper,
)
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    get_or_create_pepper,
    get_patient,
)


@pytest.fixture
def disaster_workspace(tmp_path, monkeypatch):
    """Provide isolated environment for destructive fault injection."""
    db_file = tmp_path / "fault_db.sqlite3"
    monkeypatch.setenv("MSK_LAB_DB_PATH", str(db_file))
    get_config(reload=True)
    run_migrations(db_file)
    try:
        yield db_file, tmp_path
    finally:
        monkeypatch.delenv("MSK_LAB_DB_PATH", raising=False)
        get_config(reload=True)


def test_atomic_migration_rollback_on_failure(disaster_workspace, monkeypatch):
    """Verify that a failing multi-statement migration cleanly rolls back without leaving partial tables (DEF-23)."""
    db_file, _ = disaster_workspace
    failed_version = 999
    # Multi-statement migration where first statement is valid, second fails
    bad_migration = (
        failed_version,
        "0999_fault_injection_test",
        """
        CREATE TABLE canary_table_before_crash (id INTEGER PRIMARY KEY, note TEXT);
        THIS IS DELIBERATELY INVALID SQL ERROR;
        CREATE TABLE canary_table_after_crash (id INTEGER PRIMARY KEY);
        """
    )
    monkeypatch.setattr(
        "msk_research_lab.core.migrations.MIGRATIONS",
        MIGRATIONS + [bad_migration],
    )

    with pytest.raises(MigrationError) as exc_info:
        run_migrations(db_file)

    assert f"Migration {failed_version}" in str(exc_info.value)

    # Verify atomic rollback: canary_table_before_crash must NOT exist!
    with get_db(db_file) as conn:
        tables = [
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        ]
        assert "canary_table_before_crash" not in tables
        assert "canary_table_after_crash" not in tables

        applied = get_applied_migrations(conn)
        assert failed_version not in applied


def test_key_rotation_orphan_cleanup_on_transaction_failure(disaster_workspace, monkeypatch):
    """Verify that if rotate_pepper encounters an error, candidate key file is cleaned up."""
    db_file, tmp_path = disaster_workspace
    active_pepper_file, vault_dir = get_pepper_storage_paths()
    initial_version = get_current_pepper_version(db_file)
    candidate_file = active_pepper_file.parent / ".workstation_pepper.new"

    # Monkeypatch get_pseudonym_hash to raise error during migration loop
    def fault_pseudonym_hash(*args, **kwargs):
        raise RuntimeError("Simulated power loss during patient migration loop")

    monkeypatch.setattr(
        "msk_research_lab.security.key_lifecycle.get_pseudonym_hash",
        fault_pseudonym_hash,
    )

    # Insert a patient to ensure the loop executes
    create_patient(full_name="Subject Alpha", primary_complaint="Knee instability")

    with pytest.raises(RuntimeError, match="Simulated power loss"):
        rotate_pepper(custom_path=db_file)

    # Verify that candidate file was unlinked and does NOT persist on disk
    assert not candidate_file.exists()
    # Active version must remain unchanged
    assert get_current_pepper_version(db_file) == initial_version


def test_backup_tampering_fails_closed_without_corrupting_destination(disaster_workspace):
    """Verify corrupted AES-GCM ciphertext fails closed and leaves restore dir intact (DEF-15)."""
    db_file, tmp_path = disaster_workspace
    create_patient(full_name="Subject Beta", primary_complaint="Rotator cuff")

    encrypted_file = create_encrypted_backup("super_secret_passphrase", target_export_dir=tmp_path)
    assert encrypted_file.exists()

    # Tamper with 1 byte in the ciphertext body
    raw_data = bytearray(encrypted_file.read_bytes())
    raw_data[64] ^= 0xFF
    tampered_file = tmp_path / "tampered_backup.mskenc"
    tampered_file.write_bytes(raw_data)

    restore_target = tmp_path / "restore_victim"
    restore_target.mkdir()

    with pytest.raises(BackupDecryptionError):
        restore_encrypted_backup(tampered_file, "super_secret_passphrase", target_restore_dir=restore_target)

    # Destination directory must remain clean without damaged database
    assert not (restore_target / "lab.sqlite3").exists()


def test_backup_path_traversal_archive_rejection(disaster_workspace):
    """Verify staged restore rejects archives with path traversal members (P10-B)."""
    db_file, tmp_path = disaster_workspace
    from msk_research_lab.security.openssl_gcm import aes_256_gcm_encrypt
    from msk_research_lab.security.key_lifecycle import ENC_MAGIC_V2, _derive_key_v2
    import secrets

    # Create in-memory tarball with path traversal entry
    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w:gz") as tar:
        payload = b"MALICIOUS_OVERWRITE"
        ti = tarfile.TarInfo(name="../../evil_traversal.txt")
        ti.size = len(payload)
        tar.addfile(ti, io.BytesIO(payload))

    tar_bytes = tar_buf.getvalue()

    # Encrypt malicious tarball with valid MSKENC02 container
    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    key = _derive_key_v2("legit_pass", salt)
    aad = ENC_MAGIC_V2 + salt + iv
    ciphertext, tag = aes_256_gcm_encrypt(key, iv, tar_bytes, aad=aad)

    header = ENC_MAGIC_V2 + salt + iv + tag
    malicious_pkg = tmp_path / "malicious_traversal.mskenc"
    malicious_pkg.write_bytes(header + ciphertext)

    restore_target = tmp_path / "traversal_restore_target"
    restore_target.mkdir()

    with pytest.raises(BackupDecryptionError, match="Malicious archive member detected"):
        restore_encrypted_backup(malicious_pkg, "legit_pass", target_restore_dir=restore_target)

    assert not (tmp_path / "evil_traversal.txt").exists()
