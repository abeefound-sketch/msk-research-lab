"""Parallel Source Comparator Workspace (G8 / R3-04).

Enables side-by-side original source comparison, independence tracking,
operator classification (MATCH, DIFFERENCE, UNCERTAIN, NOT_COMPARABLE),
and prevents misleading geometric millimeter calculations without landmark registration.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from msk_research_lab.core.db import get_db
from msk_research_lab.provenance.registry import (
    get_source,
    get_source_location,
    resolve_source_locator,
    check_source_independence,
    ProvenanceError,
)

ALLOWLISTED_CLASSIFICATIONS = {
    "MATCH",
    "DIFFERENCE",
    "UNCERTAIN",
    "NOT_COMPARABLE",
}


class ComparisonError(ProvenanceError):
    """Raised when source comparison inputs are invalid."""
    pass


def compare_sources(
    *,
    comparison_id: str,
    source_a_id: str,
    source_b_id: str,
    locator_a_id: Optional[str] = None,
    locator_b_id: Optional[str] = None,
    classification: str,
    operator_notes: Optional[str] = None,
    is_geometric: bool = False,
    is_frame_registered: bool = False,
) -> Dict[str, Any]:
    """Execute and freeze a side-by-side comparison between two original sources.

    Respects epistemics:
      - Independence is strictly checked (shared ancestry or mirrors flag non-independence).
      - Geometric assertions across uncalibrated/unregistered frames prohibit fake millimeter difference.
    """
    if classification not in ALLOWLISTED_CLASSIFICATIONS:
        raise ComparisonError(f"Invalid classification '{classification}'. Allowed: {sorted(ALLOWLISTED_CLASSIFICATIONS)}")

    src_a = get_source(source_a_id)
    src_b = get_source(source_b_id)
    if not src_a:
        raise ComparisonError(f"Source A '{source_a_id}' not found.")
    if not src_b:
        raise ComparisonError(f"Source B '{source_b_id}' not found.")

    # Independence analysis
    indep_info = check_source_independence(source_a_id, source_b_id)

    # Locator verification if supplied
    resolved_loc_a = None
    if locator_a_id:
        resolved_loc_a = resolve_source_locator(source_a_id, locator_a_id)
    resolved_loc_b = None
    if locator_b_id:
        resolved_loc_b = resolve_source_locator(source_b_id, locator_b_id)

    # Epistemic geometric guard
    if is_geometric and not is_frame_registered:
        geometric_state = "UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL"
    elif is_geometric and is_frame_registered:
        geometric_state = "REGISTERED_COMMON_FRAME"
    else:
        geometric_state = "TEXTUAL_NON_GEOMETRIC"

    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO comparisons (
                comparison_id, source_a_id, locator_a_id, source_b_id, locator_b_id,
                classification, operator_notes, geometric_comparability_state, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(comparison_id) DO UPDATE SET
                classification=excluded.classification,
                operator_notes=excluded.operator_notes,
                geometric_comparability_state=excluded.geometric_comparability_state;
            """,
            (
                comparison_id, source_a_id, locator_a_id, source_b_id, locator_b_id,
                classification, operator_notes, geometric_state, now_iso
            )
        )

    return get_comparison(comparison_id)


def get_comparison(comparison_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve frozen comparison report by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM comparisons WHERE comparison_id = ?;", (comparison_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)

        src_a = get_source(res["source_a_id"])
        src_b = get_source(res["source_b_id"])
        res["source_a"] = src_a
        res["source_b"] = src_b
        res["independence"] = check_source_independence(res["source_a_id"], res["source_b_id"])

        if res["locator_a_id"]:
            res["locator_a"] = get_source_location(res["locator_a_id"])
        if res["locator_b_id"]:
            res["locator_b"] = get_source_location(res["locator_b_id"])

        return res
