"""Point Inspector linking 3D Geometry, Claims, Ontology, and Citations (ATLAS-04 / R4-07).

Aggregates 3D surface anchor coordinates, multilingual ontology labels,
scholarly tri-ledger claims, library citations, and regional tissue anatomy.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from msk_research_lab.core.db import get_db
from msk_research_lab.ontology.lookup import lookup_ontology
from msk_research_lab.atlas.surface_registration import get_skin_anchor


def inspect_point(point_code: str) -> Dict[str, Any]:
    """Retrieve complete multi-layer provenance and 3D geometry for a point."""
    clean_code = point_code.strip()

    # 1. Ontology labels & aliases
    ont_hits = lookup_ontology(clean_code)
    concept = ont_hits[0] if ont_hits else {
        "concept_id": f"unregistered:{clean_code}",
        "canonical_label": clean_code,
        "aliases": [],
        "namespace": "TRADITIONAL_ACUPUNCTURE",
        "review_state": "UNREVIEWED",
    }

    # 2. 3D Placements and Skin Anchors
    placements = []
    with get_db() as conn:
        cur_pl = conn.execute(
            """
            SELECT p.*, a.face_index, a.barycentric_u, a.barycentric_v, a.barycentric_w,
                   a.surface_x, a.surface_y, a.surface_z, a.normal_x, a.normal_y, a.normal_z, a.status as anchor_status
            FROM point_placements_3d p
            LEFT JOIN skin_anchors a ON p.anchor_id = a.anchor_id
            WHERE LOWER(p.canonical_label) = LOWER(?) OR LOWER(p.concept_id) = LOWER(?);
            """,
            (clean_code, clean_code)
        )
        for r in cur_pl.fetchall():
            placements.append(dict(r))

        # 3. Claims and Evidence from Tri-Ledger
        cur_cl = conn.execute(
            """
            SELECT c.claim_id, c.statement, c.claim_kind, c.status, c.review_state,
                   c.clinical_evidence_assessment, c.reviewer_id, c.review_rationale
            FROM claims c
            WHERE c.statement LIKE ? OR c.claim_id LIKE ?;
            """,
            (f"%{clean_code}%", f"%{clean_code}%")
        )
        claims = [dict(r) for r in cur_cl.fetchall()]

        # 4. Open Contradictions
        cur_cd = conn.execute(
            """
            SELECT cd.*
            FROM contradictions cd
            JOIN claims c ON cd.claim_a_id = c.claim_id
            WHERE c.statement LIKE ? OR c.claim_id LIKE ?;
            """,
            (f"%{clean_code}%", f"%{clean_code}%")
        )
        contradictions = [dict(r) for r in cur_cd.fetchall()]

    # 5. Regional anatomical tissues
    regional_anatomy = []
    if "GB21" in clean_code.upper():
        regional_anatomy = [
            {"layer": "integumentary", "structure": "Skin over superior shoulder ridge", "status": "AVAILABLE"},
            {"layer": "muscular_superficial", "structure": "Trapezius muscle (descending fibers)", "status": "AVAILABLE"},
            {"layer": "muscular_deep", "structure": "Levator scapulae & Supraspinatus", "status": "AVAILABLE"},
            {"layer": "skeletal", "structure": "Clavicle, Acromion, C7–T1 spinous processes", "status": "AVAILABLE"},
            {"layer": "nervous", "structure": "Spinal accessory nerve (CN XI) superficial branches", "status": "AVAILABLE"},
        ]

    return {
        "point_code": clean_code,
        "concept": concept,
        "placements_3d": placements,
        "claims": claims,
        "contradictions": contradictions,
        "regional_anatomy": regional_anatomy,
        "disclaimer": "Research record only; does not imply physiological equivalence or treatment recommendation."
    }
