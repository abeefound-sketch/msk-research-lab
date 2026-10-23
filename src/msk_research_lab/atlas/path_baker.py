"""Meridian Path Baking & Multi-Camera Occlusion QA (ATLAS-02 / R4-05).

Samples continuous surface paths along skin topology, flags interior body penetration
gaps, and computes occlusion across six camera views (Front, Back, Left, Right, Oblique).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.core.db import get_db
from msk_research_lab.atlas.surface_registration import (
    Point3D,
    Triangle3D,
    project_to_triangle,
    GeometryError,
)

CAMERA_VIEWS = {
    "FRONT": Point3D(0.0, 0.0, 1.0),
    "BACK": Point3D(0.0, 0.0, -1.0),
    "LEFT": Point3D(-1.0, 0.0, 0.0),
    "RIGHT": Point3D(1.0, 0.0, 0.0),
    "OBLIQUE_TOP": Point3D(0.7071, 0.7071, 0.7071).normalize(),
    "OBLIQUE_BOTTOM": Point3D(-0.7071, -0.7071, -0.7071).normalize(),
}


def check_occlusion_for_normal(normal: Point3D, view_dir: Point3D) -> bool:
    """Test if surface normal faces away from camera view direction (occluded)."""
    # normal dot view_dir: if positive, surface faces camera; if <= 0, facing away/occluded
    return normal.dot(view_dir) <= 0.0


def bake_meridian_path(
    *,
    path_id: str,
    meridian_code: str,
    source_id: str,
    model_id: str,
    control_points: List[Point3D],
    triangles: List[Triangle3D],
    penetration_tolerance_mm: float = 25.0,
) -> Dict[str, Any]:
    """Bake meridian trajectory onto surface mesh.

    Enforces geometry epistemics:
      - Breaks paths where straight lines would penetrate through the body.
      - Never invents invisible interior connections.
    """
    if len(control_points) < 2:
        raise GeometryError("At least 2 control points required to bake a meridian path.")

    baked_segments = []
    gap_warnings = []
    has_gap = False

    for i in range(len(control_points) - 1):
        p_start = control_points[i]
        p_end = control_points[i + 1]

        # Sample intermediate points along the chord
        samples = 5
        segment_ok = True
        segment_points = [p_start.to_list()]

        for s in range(1, samples):
            t = s / samples
            chord_pt = Point3D(
                p_start.x * (1 - t) + p_end.x * t,
                p_start.y * (1 - t) + p_end.y * t,
                p_start.z * (1 - t) + p_end.z * t,
            )

            # Measure distance from chord to nearest skin triangle
            min_dist = float("inf")
            best_surf = chord_pt
            for tri in triangles:
                surf, dist, _ = project_to_triangle(chord_pt, tri)
                if dist < min_dist:
                    min_dist = dist
                    best_surf = surf

            # Check if chord dives into body interior
            if min_dist > penetration_tolerance_mm:
                segment_ok = False
                has_gap = True
                gap_warnings.append({
                    "segment_index": i,
                    "sample_fraction": t,
                    "penetration_depth_mm": round(min_dist, 2),
                    "warning": f"Chord penetrates {round(min_dist, 1)} mm into interior body volume. Straight continuity broken."
                })
                break
            else:
                segment_points.append(best_surf.to_list())

        segment_points.append(p_end.to_list())
        baked_segments.append({
            "segment_index": i,
            "status": "CONTINUOUS" if segment_ok else "DISCONTINUOUS_PENETRATION_GAP",
            "points": segment_points,
            "is_broken": not segment_ok
        })

    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO meridian_paths_3d (
                path_id, meridian_code, source_id, model_id,
                ordered_points_json, baked_segments_json,
                has_penetration_gap, gap_warnings_json, review_state, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UNREVIEWED', ?)
            ON CONFLICT(path_id) DO UPDATE SET
                ordered_points_json=excluded.ordered_points_json,
                baked_segments_json=excluded.baked_segments_json,
                has_penetration_gap=excluded.has_penetration_gap,
                gap_warnings_json=excluded.gap_warnings_json;
            """,
            (
                path_id, meridian_code, source_id, model_id,
                json.dumps([p.to_list() for p in control_points]),
                json.dumps(baked_segments),
                1 if has_gap else 0,
                json.dumps(gap_warnings),
                now_iso
            )
        )

    return {
        "path_id": path_id,
        "meridian_code": meridian_code,
        "model_id": model_id,
        "segment_count": len(baked_segments),
        "has_penetration_gap": has_gap,
        "gap_warnings": gap_warnings,
        "baked_segments": baked_segments,
    }


def evaluate_six_view_occlusion(point: Point3D, normal: Point3D) -> Dict[str, Any]:
    """Evaluate point visibility across 6 canonical camera views."""
    views = {}
    for view_name, view_vector in CAMERA_VIEWS.items():
        is_occluded = check_occlusion_for_normal(normal, view_vector)
        views[view_name] = {
            "visible": not is_occluded,
            "occluded": is_occluded,
            "normal_alignment": round(normal.dot(view_vector), 4)
        }
    return views
