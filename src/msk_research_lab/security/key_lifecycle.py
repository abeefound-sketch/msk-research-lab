"""Cryptographic key lifecycle management, HMAC pepper rotation, and encrypted backup recovery."""

import datetime
import hashlib
import hmac
import json
import os
import secrets
import shutil
import sqlite3
import struct
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db, get_db_path, init_connection
from msk_research_lab.workstation.patient_manager import (
    DEFAULT_PEPPER,
    get_or_create_pepper,
    get_pseudonym_hash,
)

ENC_MAGIC = b"MSKENC01"
PBKDF2_ROUNDS = 100_000


class KeyLifecycleError(Exception):
    """Base error for key lifecycle and pepper rotation operations."""
    pass


class BackupDecryptionError(KeyLifecycleError):
    """Raised when backup authentication fails or decryption yields corrupted data."""
    pass


def get_pepper_storage_paths() -> Tuple[Path, Path]:
    """Return primary active pepper file path and key vault directory."""
    db_dir = get_db_path().parent
    active_pepper = db_dir / ".workstation_pepper"
    vault_dir = db_dir / ".key_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return active_pepper, vault_dir


def get_current_pepper_version(custom_path: Optional[Path] = None) -> int:
    """Retrieve active pepper version from database pepper_key_store or fallback to 1."""
    try:
        with get_db(custom_path) as conn:
            cur = conn.execute("""
                SELECT MAX(version) FROM pepper_key_store WHERE status = 'ACTIVE';
            """)
            row = cur.fetchone()
            if row and row[0] is not None:
                return int(row[0])
            # Fallback to MAX(pepper_version) in patients
            cur2 = conn.execute("SELECT MAX(pepper_version) FROM patients;")
            row2 = cur2.fetchone()
            if row2 and row2[0] is not None:
                return int(row2[0])
    except Exception:
        pass
    return 1


def rotate_pepper(
    new_pepper: Optional[bytes] = None,
    operator_id: str = "SYSTEM",
    custom_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Rotate HMAC pepper to next version with transactional journaling and zero record loss.
    
    Guarantees:
    - Atomically updates pseudonym_hash and pepper_version across all patient records.
    - Preserves rollback mapping in pepper_rotation_log.
    - Archives prior key material in restricted local key vault.
    - Emits auditable tri-ledger event PEPPER_ROTATED.
    """
    active_pepper_file, vault_dir = get_pepper_storage_paths()
    current_version = get_current_pepper_version(custom_path)
    new_version = current_version + 1

    if new_pepper is None:
        new_pepper = secrets.token_bytes(32)
    elif len(new_pepper) < 16:
        raise KeyLifecycleError("Pepper must be at least 16 bytes for cryptographic adequacy.")

    now = datetime.datetime.utcnow().isoformat() + "Z"
    new_pepper_fingerprint = hashlib.sha256(new_pepper).hexdigest()

    with get_db(custom_path) as conn:
        # 1. Fetch all current patient records
        rows = conn.execute("SELECT id, pseudonym_hash, pepper_version FROM patients;").fetchall()
        migration_journal: List[Dict[str, str]] = []

        for r in rows:
            pid = r["id"]
            old_hash = r["pseudonym_hash"]
            new_hash = get_pseudonym_hash(pid, pepper=new_pepper)
            migration_journal.append({
                "patient_id": pid,
                "old_hash": old_hash,
                "new_hash": new_hash,
            })

        # 2. Deactivate previous version in key store
        conn.execute("""
            UPDATE pepper_key_store SET status = 'RETIRED' WHERE status = 'ACTIVE';
        """)

        # 3. Insert new version into pepper_key_store
        conn.execute("""
            INSERT INTO pepper_key_store (version, key_hash, status, created_at)
            VALUES (?, ?, 'ACTIVE', ?);
        """, (new_version, new_pepper_fingerprint, now))

        # 4. Atomically update patient pseudonym hashes
        for item in migration_journal:
            conn.execute("""
                UPDATE patients
                SET pseudonym_hash = ?, pepper_version = ?
                WHERE id = ?;
            """, (item["new_hash"], new_version, item["patient_id"]))

        # 5. Log rotation event into journal table
        journal_json = json.dumps({
            "migrated_records": len(migration_journal),
            "fingerprint": new_pepper_fingerprint[:16],
            "details": migration_journal,
        })
        conn.execute("""
            INSERT INTO pepper_rotation_log (
                from_version, to_version, rotated_at, records_migrated, operator_id, status, journal_json
            ) VALUES (?, ?, ?, ?, ?, 'COMPLETED', ?);
        """, (current_version, new_version, now, len(migration_journal), operator_id, journal_json))

        # 6. Audit tri-ledger entry
        conn.execute("""
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?);
        """, (
            "PEPPER_ROTATED", operator_id,
            json.dumps({
                "from_version": current_version,
                "to_version": new_version,
                "records_migrated": len(migration_journal),
                "fingerprint": new_pepper_fingerprint[:16],
            }),
        ))

    # 7. Secure file updates: archive old key, write new key atomically
    if active_pepper_file.exists():
        old_archive = vault_dir / f"pepper_v{current_version}.key"
        try:
            shutil.copy2(active_pepper_file, old_archive)
            try:
                os.chmod(old_archive, 0o600)
            except Exception:
                pass
        except Exception:
            pass

    # Atomic write for new active pepper
    tmp_pepper = active_pepper_file.parent / f".tmp_pepper_{secrets.token_hex(4)}"
    tmp_pepper.write_bytes(new_pepper)
    try:
        os.chmod(tmp_pepper, 0o600)
    except Exception:
        pass
    os.replace(tmp_pepper, active_pepper_file)

    # Also archive new key into vault
    new_archive = vault_dir / f"pepper_v{new_version}.key"
    new_archive.write_bytes(new_pepper)
    try:
        os.chmod(new_archive, 0o600)
    except Exception:
        pass

    return {
        "status": "SUCCESS",
        "from_version": current_version,
        "to_version": new_version,
        "records_migrated": len(migration_journal),
        "fingerprint": new_pepper_fingerprint,
        "rotated_at": now,
    }


# ==============================================================================
# Authenticated Envelope Encrypted Backup & Restore (AEAD via PBKDF2-HMAC-CTR)
# ==============================================================================

def _derive_keys(password: str, salt: bytes) -> Tuple[bytes, bytes]:
    """Derive 32-byte encryption key (K_enc) and 32-byte MAC key (K_mac) using PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS, dklen=64)
    return dk[:32], dk[32:]


def _ctr_stream_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """Standard CTR mode keystream generation using HMAC-SHA256 blocks with fast integer XOR."""
    if not data:
        return b""
    block_size = 32
    num_blocks = (len(data) + block_size - 1) // block_size

    keystream_chunks = []
    for i in range(num_blocks):
        counter_bytes = struct.pack(">Q", i)
        keystream_chunks.append(hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest())

    keystream = b"".join(keystream_chunks)[:len(data)]
    data_int = int.from_bytes(data, "big")
    key_int = int.from_bytes(keystream, "big")
    return (data_int ^ key_int).to_bytes(len(data), "big")


def create_encrypted_backup(
    password: str,
    target_export_dir: Optional[Path] = None,
    include_pepper: bool = True,
    include_originals: bool = False,
) -> Path:
    """Create an authenticated encrypted disaster recovery archive of SQLite DB and state.
    
    Container Structure:
    [8B Magic: MSKENC01] [16B Salt] [16B Nonce] [32B HMAC-Tag] [Ciphertext...]
    """
    if len(password) < 8:
        raise KeyLifecycleError("Backup encryption password must be at least 8 characters.")

    cfg = get_config()
    export_dir = target_export_dir or (cfg.storage.root_dir / cfg.storage.data_dir / "exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    backup_file = export_dir / f"msk_backup_encrypted_{timestamp}.enc"

    # Stage raw tar package in temporary workspace
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        staged_db = tmp_dir / "lab.sqlite3"

        # Checkpoint WAL and capture consistent snapshot using VACUUM INTO
        with get_db() as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.execute(f"VACUUM INTO '{staged_db}';")

        # Copy pepper if requested
        active_pepper_file, _ = get_pepper_storage_paths()
        if include_pepper and active_pepper_file.exists():
            shutil.copy2(active_pepper_file, tmp_dir / ".workstation_pepper")

        # Copy originals if requested and present
        if include_originals:
            originals_src = cfg.storage.root_dir / cfg.storage.data_dir / "originals"
            if originals_src.exists():
                shutil.copytree(originals_src, tmp_dir / "originals", dirs_exist_ok=True)

        # Create tar package in memory
        tar_path = tmp_dir / "bundle.tar"
        with tarfile.open(tar_path, "w") as tar:
            for item in tmp_dir.iterdir():
                if item.name != "bundle.tar":
                    tar.add(item, arcname=item.name)

        plaintext = tar_path.read_bytes()

    # Generate cryptographic randomness
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(16)
    k_enc, k_mac = _derive_keys(password, salt)

    # Encrypt
    ciphertext = _ctr_stream_xor(k_enc, nonce, plaintext)

    # Compute Authenticated Tag: HMAC-SHA256(k_mac, Header || Salt || Nonce || Ciphertext)
    tag = hmac.new(k_mac, ENC_MAGIC + salt + nonce + ciphertext, hashlib.sha256).digest()

    # Write container
    with open(backup_file, "wb") as f:
        f.write(ENC_MAGIC)
        f.write(salt)
        f.write(nonce)
        f.write(tag)
        f.write(ciphertext)

    return backup_file


def restore_encrypted_backup(
    encrypted_backup_path: Path,
    password: str,
    target_restore_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Authenticate, decrypt, and restore an encrypted backup archive."""
    if not encrypted_backup_path.exists():
        raise BackupDecryptionError(f"Backup file '{encrypted_backup_path}' does not exist.")

    with open(encrypted_backup_path, "rb") as f:
        magic = f.read(8)
        if magic != ENC_MAGIC:
            raise BackupDecryptionError("Invalid backup file: header magic mismatch.")
        salt = f.read(16)
        nonce = f.read(16)
        expected_tag = f.read(32)
        ciphertext = f.read()

    # Derive keys
    k_enc, k_mac = _derive_keys(password, salt)

    # Authenticate tag
    computed_tag = hmac.new(k_mac, ENC_MAGIC + salt + nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(expected_tag, computed_tag):
        raise BackupDecryptionError("Authentication failed: invalid passphrase or corrupted payload.")

    # Decrypt
    plaintext = _ctr_stream_xor(k_enc, nonce, ciphertext)

    # Restore tar contents
    restore_dir = target_restore_dir or get_db_path().parent
    restore_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tar_tmp = Path(tmp_dir_str) / "restored.tar"
        tar_tmp.write_bytes(plaintext)

        restored_files = []
        with tarfile.open(tar_tmp, "r") as tar:
            for member in tar.getmembers():
                # Path traversal guard
                target_path = (restore_dir / member.name).resolve()
                if not str(target_path).startswith(str(restore_dir.resolve())):
                    raise BackupDecryptionError(f"Malicious archive member detected: {member.name}")
                tar.extract(member, path=restore_dir)
                restored_files.append(member.name)

    # Verify restored SQLite DB integrity
    restored_db = restore_dir / "lab.sqlite3"
    db_verified = False
    if restored_db.exists():
        conn = init_connection(restored_db)
        try:
            res = conn.execute("PRAGMA integrity_check;").fetchone()
            db_verified = bool(res and res[0] == "ok")
        finally:
            conn.close()

    return {
        "status": "RESTORED",
        "restore_dir": str(restore_dir),
        "files_restored": restored_files,
        "db_verified": db_verified,
    }
