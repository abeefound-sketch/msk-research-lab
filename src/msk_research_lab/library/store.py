"""Document ingestion, immutable SHA-256 storage, and safety validation."""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db


class DocumentSecurityError(Exception):
    """Raised on security violation during document import."""
    pass


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def detect_file_type(file_path: Path) -> str:
    """Sniff file magic bytes to determine format."""
    with open(file_path, "rb") as f:
        header = f.read(16)

    if header.startswith(b"%PDF-"):
        return "PDF"
    elif header.startswith(b"PK\x03\x04"):
        # Could be EPUB or DOCX (both are zip archives)
        suffix = file_path.suffix.lower()
        if suffix == ".epub":
            return "EPUB"
        elif suffix == ".docx":
            return "DOCX"
        return "ZIP_ARCHIVE"
    elif file_path.suffix.lower() == ".epub":
        return "EPUB"
    elif file_path.suffix.lower() == ".docx":
        return "DOCX"
    elif file_path.suffix.lower() == ".pdf":
        return "PDF"

    return "UNKNOWN"


def store_original_document(
    source_path: Path,
    original_filename: Optional[str] = None,
    max_size_bytes: int = 100 * 1024 * 1024  # 100 MiB limit
) -> Dict[str, Any]:
    """Ingest a document into content-addressed immutable storage.

    Invariants:
    1. Size within safety threshold.
    2. Exact byte hash computed before move/copy.
    3. Storage under 2data/originals/<sha256>/<filename>.
    4. Format verified.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    size = source_path.stat().st_size
    if size > max_size_bytes:
        raise DocumentSecurityError(f"File size {size} bytes exceeds limit of {max_size_bytes} bytes.")

    file_type = detect_file_type(source_path)
    if file_type not in ["PDF", "EPUB", "DOCX"]:
        raise DocumentSecurityError(f"Unsupported document format: {file_type}. Supported: PDF, EPUB, DOCX.")

    file_hash = compute_sha256(source_path)
    filename = original_filename or source_path.name

    cfg = get_config()
    dest_dir = cfg.storage.root_dir / cfg.storage.data_dir / "originals" / file_hash
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / filename

    if not dest_file.exists():
        shutil.copy2(source_path, dest_file)

    doc_id = f"doc:sha256:{file_hash[:16]}"

    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents (id, sha256, original_filename, file_type, byte_size, storage_path)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (doc_id, file_hash, filename, file_type, size, str(dest_file))
        )
        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?);
            """,
            ("DOCUMENT_INGESTED", "OPERATOR", f'{{"doc_id": "{doc_id}", "hash": "{file_hash}", "type": "{file_type}"}}')
        )

    return {
        "document_id": doc_id,
        "sha256": file_hash,
        "filename": filename,
        "file_type": file_type,
        "byte_size": size,
        "storage_path": str(dest_file)
    }
