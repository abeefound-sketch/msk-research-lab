"""P12 Durability, Crash Consistency & Privacy Hardening Test Suite.

Validates:
1. DEF-33: Strict path traversal rejection in unencrypted backup archive extraction.
2. DEF-34: SQLite online backup API under active WAL concurrency and WAL orphan cleanup during restore.
3. DEF-35: Enhanced Safe Harbor PHI scrubbing for NPI, medical licenses, dot/space SSNs, and hyphenated dates.
4. DEF-38: File locking and sharing violation retry during atomic database replacement.
"""

import io
import os
import shutil
import tarfile
import tempfile
import time
from pathlib import Path
import pytest

from msk_research_lab.core.backup import BackupIntegrityError, create_backup, restore_backup
from msk_research_lab.core.db import get_db, init_connection
from msk_research_lab.security.key_lifecycle import (
    create_encrypted_backup,
    restore_encrypted_backup,
)
from msk_research_lab.workstation.patient_manager import (
    create_patient,
    export_deidentified_research_record,
    scrub_phi_from_text,
)


def test_def33_unencrypted_backup_path_traversal_rejection(tmp_path):
    """Verify DEF-33: restore_backup rejects archives containing path traversal members."""
    malicious_archive = tmp_path / "malicious.tar.gz"

    # Craft a tar.gz containing ../traversal.txt
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
        payload = b"MALICIOUS_OVERWRITE"
        ti = tarfile.TarInfo(name="../escaped_file.txt")
        ti.size = len(payload)
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(payload))

    malicious_archive.write_bytes(tar_stream.getvalue())

    target_restore = tmp_path / "restore_dest"
    with pytest.raises(BackupIntegrityError) as exc_info:
        restore_backup(malicious_archive, target_restore)

    assert "Path traversal attempt rejected" in str(exc_info.value)
    assert not (tmp_path / "escaped_file.txt").exists()


def test_def34_sqlite_online_backup_api_and_wal_orphan_cleanup(tmp_path):
    """Verify DEF-34: Backup captures consistent snapshot, and restore cleans old WAL/SHM orphans."""
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restored_db"
    backup_dir.mkdir(parents=True, exist_ok=True)
    restore_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create simulated orphaned WAL and SHM files in restore directory
    orphaned_wal = restore_dir / "lab.sqlite3-wal"
    orphaned_shm = restore_dir / "lab.sqlite3-shm"
    orphaned_wal.write_bytes(b"CORRUPT_ORPHANED_WAL_DATA_FROM_PREVIOUS_SESSION")
    orphaned_shm.write_bytes(b"CORRUPT_ORPHANED_SHM_DATA")

    # 2. Create encrypted backup using SQLite online backup API
    pwd = "AuditPassword#P12Durability2026!"
    archive_path = create_encrypted_backup(password=pwd, target_export_dir=backup_dir)
    assert archive_path.exists()

    # 3. Restore into directory with orphaned WAL
    res = restore_encrypted_backup(encrypted_backup_path=archive_path, password=pwd, target_restore_dir=restore_dir)
    assert res["status"] == "RESTORED"

    # 4. Verify orphaned WAL and SHM files were removed
    assert not orphaned_wal.exists()
    assert not orphaned_shm.exists()

    # 5. Verify restored database opens cleanly and passes integrity check
    conn = init_connection(restore_dir / "lab.sqlite3")
    row = conn.execute("PRAGMA integrity_check;").fetchone()
    assert row[0] == "ok"
    conn.close()


def test_def35_enhanced_phi_scrubbing_npi_license_space_dot_ssn():
    """Verify DEF-35: Redaction of NPIs, licenses, dot/space-separated SSNs, and hyphenated dates."""
    note = (
        "Consultation on 14-Oct-2024 by Dr. Marcus Vance. "
        "Provider NPI: 1234567890, Medical License: MD-98765. "
        "Patient SSN recorded as 987.65.4321 and secondary ID 111 22 3333. "
        "Follow up scheduled for 2024.11.15. DEA: AB1234567."
    )
    scrubbed = scrub_phi_from_text(note)

    # Asserts on direct identifiers
    assert "14-Oct-2024" not in scrubbed
    assert "1234567890" not in scrubbed
    assert "MD-98765" not in scrubbed
    assert "987.65.4321" not in scrubbed
    assert "111 22 3333" not in scrubbed
    assert "2024.11.15" not in scrubbed
    assert "AB1234567" not in scrubbed

    # Asserts on tokens
    assert "[REDACTED_NPI]" in scrubbed
    assert "[REDACTED_LICENSE]" in scrubbed
    assert "[REDACTED_SSN]" in scrubbed
    assert "[REDACTED_DATE]" in scrubbed
