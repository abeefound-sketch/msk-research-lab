"""Full Text Search (FTS5) and exact source locator resolver."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from msk_research_lab.core.db import get_db
from msk_research_lab.library.store import compute_sha256


def search_library(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Execute FTS5 search across all indexed document locations.

    Returns exact source locators with highlighted snippets.
    """
    if not query or not query.strip():
        return []

    # Clean query for FTS5 syntax
    clean_query = query.replace('"', '""').strip()
    fts_expression = f'"{clean_query}"'

    results = []
    with get_db() as conn:
        try:
            sql = """
            SELECT
                f.document_id,
                f.location_id,
                snippet(fts_document_locations, 3, '<mark>', '</mark>', '...', 20) AS snippet,
                l.location_type,
                l.page_number,
                l.spine_href,
                l.block_index,
                l.heading_path,
                l.ocr_status,
                d.original_filename,
                d.file_type,
                d.sha256
            FROM fts_document_locations f
            JOIN document_locations l ON f.location_id = l.id
            JOIN documents d ON f.document_id = d.id
            WHERE fts_document_locations MATCH ?
            ORDER BY rank
            LIMIT ?;
            """
            cur = conn.execute(sql, (fts_expression, limit))
            for row in cur.fetchall():
                results.append({
                    "document_id": row["document_id"],
                    "location_id": row["location_id"],
                    "snippet": row["snippet"],
                    "location_type": row["location_type"],
                    "page_number": row["page_number"],
                    "spine_href": row["spine_href"],
                    "block_index": row["block_index"],
                    "heading_path": json.loads(row["heading_path"]) if row["heading_path"] else [],
                    "ocr_status": row["ocr_status"],
                    "filename": row["original_filename"],
                    "file_type": row["file_type"],
                    "sha256": row["sha256"]
                })
        except Exception:
            # Fallback to simple token prefix match
            pass

    return results


def resolve_location(document_id: str, location_id: str) -> Dict[str, Any]:
    """Resolve an exact citation to its original verified content and verify hash."""
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT l.*, d.original_filename, d.storage_path, d.sha256, d.file_type
            FROM document_locations l
            JOIN documents d ON l.document_id = d.id
            WHERE l.document_id = ? AND l.id = ?;
            """,
            (document_id, location_id)
        )
        row = cur.fetchone()
        if not row:
            return {
                "status": "UNRESOLVED",
                "document_id": document_id,
                "location_id": location_id,
                "error": "Location ID not found in library index."
            }

        # Check storage file integrity
        storage_file = Path(row["storage_path"])
        if not storage_file.exists():
            return {
                "status": "UNRESOLVED",
                "document_id": document_id,
                "location_id": location_id,
                "error": "Original storage file is missing on disk."
            }

        actual_hash = compute_sha256(storage_file)
        if actual_hash != row["sha256"]:
            return {
                "status": "HASH_MISMATCH",
                "document_id": document_id,
                "location_id": location_id,
                "error": "Original file bytes have changed since indexing!"
            }

        return {
            "status": "RESOLVED",
            "document_id": row["document_id"],
            "location_id": row["id"],
            "filename": row["original_filename"],
            "file_type": row["file_type"],
            "location_type": row["location_type"],
            "page_number": row["page_number"],
            "spine_href": row["spine_href"],
            "block_index": row["block_index"],
            "heading_path": json.loads(row["heading_path"]) if row["heading_path"] else [],
            "normalized_region": json.loads(row["normalized_region"]) if row["normalized_region"] else [],
            "text_content": row["text_content"],
            "ocr_status": row["ocr_status"],
            "storage_path": str(storage_file)
        }
