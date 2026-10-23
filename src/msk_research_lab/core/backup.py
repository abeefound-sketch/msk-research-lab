"""Backup and disaster recovery engine for SQLite, originals, and indices."""

import os
import tarfile
import json
import time
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db, init_connection
from msk_research_lab.library.store import compute_sha256


class BackupIntegrityError(Exception):
    """Raised when backup manifest verification fails."""
    pass


def create_backup(target_export_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Create a verified, consistent backup package of SQLite DB and originals."""
    cfg = get_config()
    export_dir = target_export_dir or (cfg.storage.root_dir / cfg.storage.data_dir / "exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    backup_id = f"backup_{timestamp}"
    staging_dir = export_dir / backup_id
    staging_dir.mkdir(parents=True, exist_ok=True)

    db_src = cfg.storage.root_dir / cfg.storage.db_path
    originals_src = cfg.storage.root_dir / cfg.storage.data_dir / "originals"

    manifest_files = {}

    # 1. Consistent SQLite backup using VACUUM INTO or sqlite3 online backup API
    staged_db = staging_dir / "lab.sqlite3"
    with get_db() as conn:
        conn.execute(f"VACUUM INTO '{staged_db}';")
    manifest_files["lab.sqlite3"] = compute_sha256(staged_db)

    # 2. Copy originals
    staged_originals = staging_dir / "originals"
    if originals_src.exists():
        shutil.copytree(originals_src, staged_originals, dirs_exist_ok=True)
        for orig in staged_originals.glob("**/*"):
            if orig.is_file():
                rel_path = str(orig.relative_to(staging_dir))
                manifest_files[rel_path] = compute_sha256(orig)

    # 3. Create backup manifest
    manifest_data = {
        "backup_id": backup_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema_version": "3.0",
        "file_count": len(manifest_files),
        "files": manifest_files
    }
    manifest_path = staging_dir / "backup_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 4. Pack into .tar.gz archive
    archive_path = export_dir / f"{backup_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(staging_dir, arcname=backup_id)

    # Cleanup staging directory
    shutil.rmtree(staging_dir)

    return {
        "backup_id": backup_id,
        "archive_path": str(archive_path),
        "archive_sha256": compute_sha256(archive_path),
        "file_count": len(manifest_files)
    }


def restore_backup(archive_path: Path, target_restore_dir: Path) -> Dict[str, Any]:
    """Restore backup archive to a fresh directory and verify SHA-256 integrity and SQLite health."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Backup archive {archive_path} does not exist.")

    target_restore_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=target_restore_dir)

    # Find extracted folder
    backup_dirs = [d for d in target_restore_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
    if not backup_dirs:
        raise BackupIntegrityError("No valid backup directory found inside archive.")
    root_extracted = backup_dirs[0]

    manifest_file = root_extracted / "backup_manifest.json"
    if not manifest_file.exists():
        raise BackupIntegrityError("backup_manifest.json missing from restored archive.")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Verify SHA-256 of every restored file
    mismatches = []
    for rel_path, expected_hash in manifest_data.get("files", {}).items():
        restored_file = root_extracted / rel_path
        if not restored_file.exists():
            mismatches.append(f"MISSING: {rel_path}")
            continue
        actual_hash = compute_sha256(restored_file)
        if actual_hash != expected_hash:
            mismatches.append(f"TAMPERED: {rel_path} (expected {expected_hash}, got {actual_hash})")

    if mismatches:
        raise BackupIntegrityError(f"Integrity check failed on {len(mismatches)} file(s): {', '.join(mismatches)}")

    # Verify SQLite DB in restored directory
    restored_db = root_extracted / "lab.sqlite3"
    conn = init_connection(restored_db)
    integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0] == "ok"
    # Test FTS5 query on restored DB
    fts_works = False
    try:
        cur = conn.execute("SELECT count(*) FROM fts_document_locations;")
        _ = cur.fetchone()[0]
        fts_works = True
    except Exception:
        pass
    conn.close()

    if not integrity or not fts_works:
        raise BackupIntegrityError("Restored SQLite database failed integrity check or FTS5 is broken.")

    return {
        "status": "RESTORE_VERIFIED",
        "backup_id": manifest_data.get("backup_id"),
        "restored_path": str(root_extracted),
        "verified_file_count": len(manifest_data.get("files", {})),
        "sqlite_integrity_ok": integrity,
        "fts5_functional": fts_works
    }
