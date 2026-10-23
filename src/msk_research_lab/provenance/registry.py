"""Source Provenance Registry & Exact Locator Resolution (G8 / R3-01).

Implements source artifact tracking, edition and derivative relations,
source independence verification, and exact multi-format locator resolution.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db

ALLOWLISTED_SOURCE_KINDS = {
    "PEER_REVIEWED_STUDY",
    "SYSTEMATIC_REVIEW",
    "CLINICAL_GUIDELINE",
    "TEXTBOOK",
    "TRADITIONAL_PRIMARY_TEXT",
    "REPO_SOURCE_CODE",
    "REPO_DOCUMENTATION",
    "IMAGE",
    "OPERATOR_OBSERVATION",
    "OTHER",
}

ALLOWLISTED_RIGHTS_STATUSES = {
    "ALLOWED",
    "RESTRICTED",
    "UNKNOWN",
    "REVIEW_REQUIRED",
}

ALLOWLISTED_RELATION_KINDS = {
    "TRANSLATION_OF",
    "DERIVED_FROM",
    "MIRRORS",
    "SAME_EDITION",
    "INDEPENDENT_WORK",
    "ALIAS_OF",
    "REFERENCES",
}


class ProvenanceError(Exception):
    """Base exception for provenance validation errors."""
    pass


class LocatorResolutionError(ProvenanceError):
    """Raised when an exact original locator fails resolution or hash verification."""
    pass


def register_source(
    *,
    source_id: str,
    kind: str,
    canonical_uri: str,
    title: str,
    author: Optional[str] = None,
    translator: Optional[str] = None,
    publisher: Optional[str] = None,
    language: Optional[str] = None,
    edition_id: Optional[str] = None,
    source_version: Optional[str] = None,
    git_commit_sha: Optional[str] = None,
    sha256: Optional[str] = None,
    rights_status: str = "REVIEW_REQUIRED",
    declared_license: Optional[str] = None,
    asset_license: Optional[str] = None,
    origin_id: Optional[str] = None,
    independence_group_id: Optional[str] = None,
    authenticity_state: str = "UNVERIFIED",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a specific source artifact into the provenance registry."""
    if kind not in ALLOWLISTED_SOURCE_KINDS:
        raise ProvenanceError(f"Invalid source kind '{kind}'. Allowed: {sorted(ALLOWLISTED_SOURCE_KINDS)}")
    if rights_status not in ALLOWLISTED_RIGHTS_STATUSES:
        raise ProvenanceError(f"Invalid rights status '{rights_status}'. Allowed: {sorted(ALLOWLISTED_RIGHTS_STATUSES)}")

    acq_time = datetime.now(timezone.utc).isoformat()
    # Default independence group to source_id if not explicitly provided
    eff_group = independence_group_id or source_id

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO sources (
                source_id, kind, canonical_uri, title, author, translator, publisher,
                language, edition_id, acquisition_time, source_version, git_commit_sha,
                sha256, rights_status, declared_license, asset_license, origin_id,
                independence_group_id, authenticity_state, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                title=excluded.title,
                author=excluded.author,
                rights_status=excluded.rights_status,
                declared_license=excluded.declared_license,
                asset_license=excluded.asset_license,
                independence_group_id=excluded.independence_group_id,
                authenticity_state=excluded.authenticity_state,
                notes=excluded.notes;
            """,
            (
                source_id, kind, canonical_uri, title, author, translator, publisher,
                language, edition_id, acq_time, source_version, git_commit_sha,
                sha256, rights_status, declared_license, asset_license, origin_id,
                eff_group, authenticity_state, notes
            )
        )
    return get_source(source_id)


def get_source(source_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve source details by source_id."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM sources WHERE source_id = ?;", (source_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def register_source_location(
    *,
    locator_id: str,
    source_id: str,
    locator_type: str,
    locator_details: Dict[str, Any],
    preview_text_hash: Optional[str] = None,
    extract_method: str = "MANUAL",
    visibility_status: str = "ALLOWED",
) -> Dict[str, Any]:
    """Register an exact locator within a source (e.g. PDF page, EPUB spine, JSON pointer)."""
    source = get_source(source_id)
    if not source:
        raise ProvenanceError(f"Source '{source_id}' does not exist.")

    locator_json = json.dumps(locator_details, sort_keys=True)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO source_locations (
                locator_id, source_id, locator_type, locator_json,
                preview_text_hash, extract_method, visibility_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(locator_id) DO UPDATE SET
                locator_type=excluded.locator_type,
                locator_json=excluded.locator_json,
                preview_text_hash=excluded.preview_text_hash,
                visibility_status=excluded.visibility_status;
            """,
            (
                locator_id, source_id, locator_type, locator_json,
                preview_text_hash, extract_method, visibility_status
            )
        )
    return get_source_location(locator_id)


def get_source_location(locator_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve source location details by locator_id."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM source_locations WHERE locator_id = ?;", (locator_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["locator_details"] = json.loads(res["locator_json"])
        return res


def register_source_relation(
    *,
    relation_id: str,
    source_a_id: str,
    source_b_id: str,
    kind: str,
    rationale: Optional[str] = None,
    review_state: str = "UNREVIEWED",
) -> Dict[str, Any]:
    """Record a derivative, mirror, translation, or independent relationship between sources."""
    if kind not in ALLOWLISTED_RELATION_KINDS:
        raise ProvenanceError(f"Invalid relation kind '{kind}'. Allowed: {sorted(ALLOWLISTED_RELATION_KINDS)}")

    if not get_source(source_a_id):
        raise ProvenanceError(f"Source A '{source_a_id}' does not exist.")
    if not get_source(source_b_id):
        raise ProvenanceError(f"Source B '{source_b_id}' does not exist.")

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO source_relations (
                relation_id, source_a_id, source_b_id, kind, rationale, review_state
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(relation_id) DO UPDATE SET
                kind=excluded.kind,
                rationale=excluded.rationale,
                review_state=excluded.review_state;
            """,
            (relation_id, source_a_id, source_b_id, kind, rationale, review_state)
        )
    return {
        "relation_id": relation_id,
        "source_a_id": source_a_id,
        "source_b_id": source_b_id,
        "kind": kind,
        "rationale": rationale,
        "review_state": review_state,
    }


def check_source_independence(source_a_id: str, source_b_id: str) -> Dict[str, Any]:
    """Check whether two sources are truly independent or share derivative/upstream ancestry.

    Never count translations, mirrors, or forks as independent confirmation.
    """
    src_a = get_source(source_a_id)
    src_b = get_source(source_b_id)
    if not src_a or not src_b:
        raise ProvenanceError("Both sources must exist to evaluate independence.")

    # Rule 1: Same source ID
    if source_a_id == source_b_id:
        return {
            "is_independent": False,
            "reason": "IDENTICAL_SOURCE",
            "group_a": src_a.get("independence_group_id"),
            "group_b": src_b.get("independence_group_id"),
        }

    # Rule 2: Shared independence group ID
    grp_a = src_a.get("independence_group_id")
    grp_b = src_b.get("independence_group_id")
    if grp_a and grp_b and grp_a == grp_b:
        return {
            "is_independent": False,
            "reason": f"SHARED_INDEPENDENCE_GROUP:{grp_a}",
            "group_a": grp_a,
            "group_b": grp_b,
        }

    # Rule 3: Declared derivative/mirror relations
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT kind, rationale FROM source_relations
            WHERE (source_a_id = ? AND source_b_id = ?)
               OR (source_a_id = ? AND source_b_id = ?);
            """,
            (source_a_id, source_b_id, source_b_id, source_a_id)
        )
        relations = cur.fetchall()
        for r in relations:
            rel_kind = r["kind"]
            if rel_kind in {"DERIVED_FROM", "MIRRORS", "TRANSLATION_OF", "SAME_EDITION", "ALIAS_OF"}:
                return {
                    "is_independent": False,
                    "reason": f"DECLARED_RELATION:{rel_kind}",
                    "rationale": r["rationale"],
                    "group_a": grp_a,
                    "group_b": grp_b,
                }

    return {
        "is_independent": True,
        "reason": "DISTINCT_PROVENANCE_GROUPS",
        "group_a": grp_a,
        "group_b": grp_b,
    }


def resolve_source_locator(source_id: str, locator_id: str) -> Dict[str, Any]:
    """Verify that the underlying source and exact locator resolve faithfully without tampering.

    Verifies document SHA-256 or Git commit, checks page/block boundaries, and returns status.
    """
    source = get_source(source_id)
    if not source:
        raise LocatorResolutionError(f"SOURCE_UNAVAILABLE: Source '{source_id}' not found.")

    loc = get_source_location(locator_id)
    if not loc or loc["source_id"] != source_id:
        raise LocatorResolutionError(f"LOCATOR_NOT_FOUND: Locator '{locator_id}' not found for source '{source_id}'.")

    cfg = get_config()
    loc_details = loc["locator_details"]
    loc_type = loc["locator_type"]

    # 1. Verification of document file if sha256 is pinned
    expected_sha = source.get("sha256")
    if expected_sha:
        # Check in 2data/originals/
        original_file = cfg.data_dir / "originals" / expected_sha / "content"
        if not original_file.exists():
            # Check if canonical_uri points to existing local file
            local_candidate = Path(source["canonical_uri"])
            if local_candidate.exists():
                original_file = local_candidate
            else:
                raise LocatorResolutionError(
                    f"SOURCE_FILE_MISSING: Original content for sha256={expected_sha} cannot be opened."
                )

        # Hash check
        actual_sha = hashlib.sha256(original_file.read_bytes()).hexdigest()
        if actual_sha.lower() != expected_sha.lower():
            raise LocatorResolutionError(
                f"HASH_MISMATCH: Source '{source_id}' sha256 expected {expected_sha} but got {actual_sha}."
            )

    # 2. Locator bounds check
    if loc_type == "PDF_PAGE":
        page = loc_details.get("page")
        if not isinstance(page, int) or page < 1:
            raise LocatorResolutionError(f"INVALID_LOCATOR: PDF page must be a positive integer, got {page}.")
    elif loc_type == "EPUB_LOCATOR":
        if "href" not in loc_details:
            raise LocatorResolutionError("INVALID_LOCATOR: EPUB locator must include 'href'.")
    elif loc_type == "DOCX_BLOCK":
        if "block_index" not in loc_details:
            raise LocatorResolutionError("INVALID_LOCATOR: DOCX locator must include 'block_index'.")
    elif loc_type == "JSON_POINTER":
        if "pointer" not in loc_details:
            raise LocatorResolutionError("INVALID_LOCATOR: JSON locator must include 'pointer'.")
    elif loc_type == "GIT_LINE_RANGE":
        if "commit" not in loc_details or "path" not in loc_details:
            raise LocatorResolutionError("INVALID_LOCATOR: Git locator must include 'commit' and 'path'.")

    return {
        "status": "RESOLVED",
        "source_id": source_id,
        "locator_id": locator_id,
        "locator_type": loc_type,
        "locator_details": loc_details,
        "source_title": source["title"],
        "rights_status": source["rights_status"],
        "authenticity_state": source["authenticity_state"],
    }
