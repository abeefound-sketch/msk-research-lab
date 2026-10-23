"""Two-Source 3D Placement Comparative Adapter (ATLAS-03 / R4-06).

Enforces geometric epistemics:
  - Unregistered coordinate frames prohibit fake millimeter difference.
  - Returns NOT_COMPARABLE when landmark registration is absent.
  - Reports displacement metrics only when a shared reference frame is established.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from msk_research_lab.atlas.surface_registration import Point3D, GeometryError


def compare_placements_3d(
    *,
    point_code: str,
    placement_a: Dict[str, Any],
    placement_b: Dict[str, Any],
    tolerance_mm: float = 5.0,
) -> Dict[str, Any]:
    """Compare two source placements for an acupuncture or somatic landmark."""
    src_a = placement_a.get("source_id", "source_a")
    src_b = placement_b.get("source_id", "source_b")
    model_a = placement_a.get("model_id")
    model_b = placement_b.get("model_id")

    reg_a = placement_a.get("frame_registered", False)
    reg_b = placement_b.get("frame_registered", False)

    # 1. Epistemic Guard: If models differ and common landmark registration is absent
    if (model_a != model_b) and (not reg_a or not reg_b):
        return {
            "point_code": point_code,
            "source_a": src_a,
            "source_b": src_b,
            "model_a": model_a,
            "model_b": model_b,
            "classification": "NOT_COMPARABLE",
            "geometric_comparability_state": "UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL",
            "measured_distance_mm": None,
            "displacement_vector": None,
            "reason": (
                f"Source A uses model '{model_a}' and Source B uses model '{model_b}' "
                "without verified anatomical landmark registration. "
                "Numeric millimeter subtraction across unaligned frames is prohibited."
            )
        }

    # 2. Both placements are registered to a common frame
    pt_a = Point3D(placement_a["x"], placement_a["y"], placement_a["z"])
    pt_b = Point3D(placement_b["x"], placement_b["y"], placement_b["z"])

    dx = round(pt_b.x - pt_a.x, 3)
    dy = round(pt_b.y - pt_a.y, 3)
    dz = round(pt_b.z - pt_a.z, 3)
    dist = round(pt_a.distance_to(pt_b), 3)

    is_match = dist <= tolerance_mm
    classification = "MATCH" if is_match else "DIFFERENCE"

    return {
        "point_code": point_code,
        "source_a": src_a,
        "source_b": src_b,
        "model_a": model_a,
        "model_b": model_b,
        "classification": classification,
        "geometric_comparability_state": "REGISTERED_COMMON_FRAME",
        "measured_distance_mm": dist,
        "tolerance_mm": tolerance_mm,
        "displacement_vector": {"dx": dx, "dy": dy, "dz": dz},
        "reason": f"Positions compared within registered common frame. Displacement: {dist} mm."
    }
