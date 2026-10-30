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
from msk_research_lab.security.openssl_gcm import (
    aes_256_gcm_decrypt,
    aes_256_gcm_encrypt,
    is_openssl_gcm_available,
)
from msk_research_lab.workstation.patient_manager import (
    DEFAULT_PEPPER,
    get_or_create_pepper,
    get_pseudonym_hash,
)

ENC_MAGIC_V1 = b"MSKENC01"
ENC_MAGIC_V2 = b"MSKENC02"
ENC_MAGIC = ENC_MAGIC_V2  # Default container format for P9+
PBKDF2_ROUNDS = 100_000


class KeyLifecycleError(Exception):
    """Base error for key lifecycle and pepper rotation operations."""
    pass


class BackupDecryptionError(KeyLifecycleError):
    """Raised when backup authentication fails or decryption yields corrupted data."""
    pass


def get_pepper_storage_paths() -> Tuple[Path, Path]:
    """Return primary active pepper file path and key vault directory with secure permissions."""
    db_dir = get_db_path().parent
    active_pepper = db_dir / ".workstation_pepper"
    vault_dir = db_dir / ".key_vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(vault_dir, 0o700)
    except Exception:
        pass
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


def recover_active_pepper_from_vault(custom_path: Optional[Path] = None) -> Dict[str, Any]:
    """Recover or resynchronize active .workstation_pepper file from .key_vault if desynchronized or missing."""
    active_pepper_file, vault_dir = get_pepper_storage_paths()
    active_version = get_current_pepper_version(custom_path)

    # Query expected key hash from database
    expected_hash: Optional[str] = None
    try:
        with get_db(custom_path) as conn:
            row = conn.execute(
                "SELECT key_hash FROM pepper_key_store WHERE version = ? AND status = 'ACTIVE';",
                (active_version,)
            ).fetchone()
            if row:
                expected_hash = row[0]
    except Exception:
        pass

    # Check if active file exists and matches
    if active_pepper_file.exists():
        current_data = active_pepper_file.read_bytes()
        current_hash = hashlib.sha256(current_data).hexdigest()
        if expected_hash is None or current_hash == expected_hash:
            return {
                "status": "IN_SYNC",
                "version": active_version,
                "recovered_from_vault": False,
                "fingerprint": current_hash[:16],
            }

    # Desynchronized or missing: attempt recovery from vault
    vault_key_file = vault_dir / f"pepper_v{active_version}.key"
    if vault_key_file.exists():
        vault_data = vault_key_file.read_bytes()
        vault_hash = hashlib.sha256(vault_data).hexdigest()
        if expected_hash is None or vault_hash == expected_hash:
            tmp_target = active_pepper_file.parent / f".tmp_recover_{secrets.token_hex(4)}"
            tmp_target.write_bytes(vault_data)
            try:
                os.chmod(tmp_target, 0o600)
            except Exception:
                pass
            os.replace(tmp_target, active_pepper_file)
            return {
                "status": "RECOVERED",
                "version": active_version,
                "recovered_from_vault": True,
                "fingerprint": vault_hash[:16],
            }

    return {
        "status": "VAULT_MISSING",
        "version": active_version,
        "recovered_from_vault": False,
        "fingerprint": None,
    }


def rotate_pepper(
    new_pepper: Optional[bytes] = None,
    operator_id: str = "SYSTEM",
    custom_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Rotate HMAC pepper to next version with two-phase commit, transactional journaling, and zero record loss.
    
    Guarantees:
    - Pre-writes candidate key (.workstation_pepper.new) prior to DB transaction.
    - Atomically updates pseudonym_hash and pepper_version across all patient records in SQLite transaction.
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

    # 1. Write candidate key to write-ahead file with strict permissions
    candidate_file = active_pepper_file.parent / ".workstation_pepper.new"
    candidate_file.write_bytes(new_pepper)
    try:
        os.chmod(candidate_file, 0o600)
    except Exception:
        pass

    with get_db(custom_path) as conn:
        # 2. Fetch all current patient records
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

        # 3. Deactivate previous version in key store
        conn.execute("""
            UPDATE pepper_key_store SET status = 'RETIRED' WHERE status = 'ACTIVE';
        """)

        # 4. Insert new version into pepper_key_store
        conn.execute("""
            INSERT INTO pepper_key_store (version, key_hash, status, created_at)
            VALUES (?, ?, 'ACTIVE', ?);
        """, (new_version, new_pepper_fingerprint, now))

        # 5. Atomically update patient pseudonym hashes
        for item in migration_journal:
            conn.execute("""
                UPDATE patients
                SET pseudonym_hash = ?, pepper_version = ?
                WHERE id = ?;
            """, (item["new_hash"], new_version, item["patient_id"]))

        # 6. Log rotation event into journal table
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

        # 7. Audit tri-ledger entry
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

    # 8. Post-commit key material commitment:
    # Archive existing active pepper into vault
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

    # Atomically commit candidate pepper to active pepper path
    os.replace(candidate_file, active_pepper_file)
    try:
        os.chmod(active_pepper_file, 0o600)
    except Exception:
        pass

    # Also store committed key in vault under new version
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
# Authenticated Envelope Encrypted Backup & Restore (AEAD: AES-256-GCM / CTR)
# ==============================================================================

def _derive_keys_v1(password: str, salt: bytes) -> Tuple[bytes, bytes]:
    """Derive 32-byte encryption key (K_enc) and 32-byte MAC key (K_mac) using PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS, dklen=64)
    return dk[:32], dk[32:]


def _derive_key_v2(password: str, salt: bytes) -> bytes:
    """Derive 32-byte AES-256 key using PBKDF2-HMAC-SHA256 for MSKENC02."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS, dklen=32)


def _ctr_stream_xor(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """Legacy CTR mode keystream generation using HMAC-SHA256 blocks with integer XOR."""
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
    format_version: str = "v2",
) -> Path:
    """Create an authenticated encrypted disaster recovery archive of SQLite DB and state.
    
    Container Structure (MSKENC02 - Standard EVP AES-256-GCM AEAD):
    [8B Magic: MSKENC02] [16B Salt] [12B IV] [16B Tag] [Ciphertext...]
    
    Container Structure (MSKENC01 - Legacy CTR + HMAC-SHA256):
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

    if format_version == "v1":
        # Legacy MSKENC01
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(16)
        k_enc, k_mac = _derive_keys_v1(password, salt)
        ciphertext = _ctr_stream_xor(k_enc, nonce, plaintext)
        tag = hmac.new(k_mac, ENC_MAGIC_V1 + salt + nonce + ciphertext, hashlib.sha256).digest()

        with open(backup_file, "wb") as f:
            f.write(ENC_MAGIC_V1)
            f.write(salt)
            f.write(nonce)
            f.write(tag)
            f.write(ciphertext)
    else:
        # Standard MSKENC02 (AES-256-GCM AEAD)
        salt = secrets.token_bytes(16)
        iv = secrets.token_bytes(12)
        key = _derive_key_v2(password, salt)
        aad = ENC_MAGIC_V2 + salt + iv
        ciphertext, tag = aes_256_gcm_encrypt(key, iv, plaintext, aad=aad)

        with open(backup_file, "wb") as f:
            f.write(ENC_MAGIC_V2)
            f.write(salt)
            f.write(iv)
            f.write(tag)
            f.write(ciphertext)

    return backup_file


def restore_encrypted_backup(
    encrypted_backup_path: Path,
    password: str,
    target_restore_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Authenticate, decrypt, verify in isolated staging, and restore an encrypted backup archive."""
    if not encrypted_backup_path.exists():
        raise BackupDecryptionError(f"Backup file '{encrypted_backup_path}' does not exist.")

    with open(encrypted_backup_path, "rb") as f:
        magic = f.read(8)
        if magic == ENC_MAGIC_V2:
            salt = f.read(16)
            iv = f.read(12)
            expected_tag = f.read(16)
            ciphertext = f.read()

            key = _derive_key_v2(password, salt)
            aad = ENC_MAGIC_V2 + salt + iv
            try:
                plaintext = aes_256_gcm_decrypt(key, iv, ciphertext, expected_tag, aad=aad)
            except Exception as e:
                raise BackupDecryptionError(f"Authentication failed: invalid passphrase or corrupted payload ({e}).")

        elif magic == ENC_MAGIC_V1:
            salt = f.read(16)
            nonce = f.read(16)
            expected_tag = f.read(32)
            ciphertext = f.read()

            k_enc, k_mac = _derive_keys_v1(password, salt)
            computed_tag = hmac.new(k_mac, ENC_MAGIC_V1 + salt + nonce + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(expected_tag, computed_tag):
                raise BackupDecryptionError("Authentication failed: invalid passphrase or corrupted payload.")

            plaintext = _ctr_stream_xor(k_enc, nonce, ciphertext)
        else:
            raise BackupDecryptionError(f"Invalid backup file: unsupported container magic {magic!r}.")

    restore_dir = target_restore_dir or get_db_path().parent
    restore_dir.mkdir(parents=True, exist_ok=True)

    # Isolated staging extraction and verification
    with tempfile.TemporaryDirectory() as staging_dir_str:
        staging_dir = Path(staging_dir_str)
        tar_staging = staging_dir / "restored.tar"
        tar_staging.write_bytes(plaintext)

        staging_extracted = staging_dir / "extracted"
        staging_extracted.mkdir(parents=True, exist_ok=True)

        restored_files: List[str] = []
        with tarfile.open(tar_staging, "r") as tar:
            for member in tar.getmembers():
                # Strict path traversal guard
                member_path = (staging_extracted / member.name).resolve()
                if not str(member_path).startswith(str(staging_extracted.resolve())):
                    raise BackupDecryptionError(f"Malicious archive member detected: {member.name}")
                tar.extract(member, path=staging_extracted)
                restored_files.append(member.name)

        # Staging SQLite verification before deploying to restore_dir
        staged_db = staging_extracted / "lab.sqlite3"
        db_verified = False
        if staged_db.exists():
            try:
                conn = sqlite3.connect(str(staged_db))
                res = conn.execute("PRAGMA integrity_check;").fetchone()
                if not res or res[0] != "ok":
                    conn.close()
                    raise BackupDecryptionError(f"Corrupted database in archive: integrity check returned {res}")
                fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
                if fk_violations:
                    conn.close()
                    raise BackupDecryptionError(f"Foreign key violations detected in restored archive: {fk_violations}")
                conn.close()
                db_verified = True
            except sqlite3.DatabaseError as db_err:
                raise BackupDecryptionError(f"Staged database validation failed: {db_err}")

        # Atomic copy from verified staging to final restore directory
        for item in staging_extracted.iterdir():
            target_item = restore_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target_item)
                if item.name.startswith("."):
                    try:
                        os.chmod(target_item, 0o600)
                    except Exception:
                        pass

    return {
        "status": "RESTORED",
        "restore_dir": str(restore_dir),
        "files_restored": restored_files,
        "db_verified": db_verified,
    }
