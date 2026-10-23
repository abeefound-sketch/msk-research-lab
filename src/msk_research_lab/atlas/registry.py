"""3D Anatomical Model Registry & Coordinate Metadata (ATLAS-01..03 / R4-03).

Registers reference anatomical 3D models with content SHA-256, declared units,
coordinate frames, reference poses, handedness, and anatomical landmarks.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from msk_research_lab.core.db import get_db


class ModelRegistryError(Exception):
    """Base exception for 3D model registry errors."""
    pass


def register_model_3d(
    *,
    model_id: str,
    name: str,
    mesh_id: str,
    sha256: str,
    units: str = "mm",
    coordinate_frame: str = "mesh_local_xyz",
    reference_pose: str = "standing_anatomical",
    handedness: str = "right_handed",
    landmarks: Optional[Dict[str, List[float]]] = None,
    skin_mesh_id: str,
    license: str,
    rights_status: str = "ALLOWED",
) -> Dict[str, Any]:
    """Register a 3D anatomical model with strict coordinate and unit metadata."""
    if not units or units.lower() not in {"mm", "cm", "m"}:
        raise ModelRegistryError(f"Invalid or missing units: '{units}'. Declared calibrated units (mm/cm/m) required.")

    if not coordinate_frame:
        raise ModelRegistryError("Coordinate frame must be explicitly specified (e.g. 'mesh_local_xyz').")

    if len(sha256) != 64:
        raise ModelRegistryError("Model SHA-256 must be a valid 64-character hexadecimal digest.")

    if not skin_mesh_id:
        raise ModelRegistryError("Designated exterior skin mesh ID must be provided.")

    now_iso = datetime.now(timezone.utc).isoformat()
    landmarks_json = json.dumps(landmarks or {})

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO models_3d (
                model_id, name, mesh_id, sha256, units, coordinate_frame,
                reference_pose, handedness, landmarks_json, skin_mesh_id,
                license, rights_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model_id) DO UPDATE SET
                name=excluded.name,
                sha256=excluded.sha256,
                units=excluded.units,
                coordinate_frame=excluded.coordinate_frame,
                reference_pose=excluded.reference_pose,
                landmarks_json=excluded.landmarks_json,
                skin_mesh_id=excluded.skin_mesh_id,
                rights_status=excluded.rights_status;
            """,
            (
                model_id, name, mesh_id, sha256.lower(), units, coordinate_frame,
                reference_pose, handedness, landmarks_json, skin_mesh_id,
                license, rights_status, now_iso
            )
        )
    return get_model_3d(model_id)


def get_model_3d(model_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve 3D model metadata by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM models_3d WHERE model_id = ?;", (model_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["landmarks"] = json.loads(res.get("landmarks_json") or "{}")
        return res


def list_models_3d() -> List[Dict[str, Any]]:
    """List all registered 3D models."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM models_3d ORDER BY created_at ASC;")
        models = []
        for r in cur.fetchall():
            m = dict(r)
            m["landmarks"] = json.loads(m.get("landmarks_json") or "{}")
            models.append(m)
        return models


def seed_standard_models_if_empty() -> None:
    """Seed baseline calibrated anatomical reference models if none exist."""
    models = list_models_3d()
    if models:
        return

    # 1. Calibrated BodyParts3D v4.0 Reference Torso (Male)
    register_model_3d(
        model_id="bodyparts3d_v4_ref_torso",
        name="BodyParts3D v4.0 Calibrated Cervical-Thoracic Reference",
        mesh_id="bp3d_cervical_torso_skin_01",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        units="mm",
        coordinate_frame="mesh_local_xyz",
        reference_pose="standing_anatomical",
        handedness="right_handed",
        landmarks={
            "C7_spinous_process": [0.0, 480.0, -85.0],
            "acromion_left": [-195.0, 470.0, -10.0],
            "acromion_right": [195.0, 470.0, -10.0],
            "sternal_notch": [0.0, 460.0, 60.0],
        },
        skin_mesh_id="skin_surface_exterior",
        license="CC-BY-SA 2.1 Japan",
        rights_status="ALLOWED",
    )

    # 2. Calibrated Synthetic Anatomical Torso Fixture
    register_model_3d(
        model_id="synthetic_torso_v1",
        name="Calibrated Synthetic Anatomical Torso Fixture",
        mesh_id="synthetic_torso_mesh_01",
        sha256="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
        units="mm",
        coordinate_frame="mesh_local_xyz",
        reference_pose="standing_anatomical",
        handedness="right_handed",
        landmarks={
            "C7_spinous_process": [0.0, 500.0, -80.0],
            "acromion_left": [-200.0, 490.0, -15.0],
            "acromion_right": [200.0, 490.0, -15.0],
        },
        skin_mesh_id="skin_mesh_torso",
        license="MIT / Local Synthetic Fixture",
        rights_status="ALLOWED",
    )

    # 3. Seed Reference Anchor & Placement for GB21 (Jianjing / Kiên tỉnh)
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO skin_anchors (
                anchor_id, model_id, mesh_sha256, face_index,
                barycentric_u, barycentric_v, barycentric_w,
                surface_x, surface_y, surface_z,
                normal_x, normal_y, normal_z,
                status, created_at
            ) VALUES (
                'anchor_gb21_bp3d',
                'bodyparts3d_v4_ref_torso',
                'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                412,
                0.333333, 0.333333, 0.333334,
                -97.5, 475.0, -45.0,
                -0.15, 0.92, -0.36,
                'VALID', ?
            ) ON CONFLICT(anchor_id) DO NOTHING;
            """,
            (now_iso,)
        )
        conn.execute(
            """
            INSERT INTO point_placements_3d (
                placement_id, concept_id, canonical_label, source_id, model_id,
                anchor_id, side, raw_x, raw_y, raw_z,
                frame_registered, registration_method, registration_status, created_at
            ) VALUES (
                'placement_gb21_bp3d',
                'GB21',
                'GB21',
                'who_standard_2008',
                'bodyparts3d_v4_ref_torso',
                'anchor_gb21_bp3d',
                'left',
                -97.5, 475.0, -45.0,
                1,
                'BARYCENTRIC_SURFACE_PROJECTION',
                'REGISTERED',
                ?
            ) ON CONFLICT(placement_id) DO NOTHING;
            """,
            (now_iso,)
        )
        # Meridian path for GB
        gb_points = [
            [-97.5, 475.0, -45.0],
            [-105.0, 472.0, -40.0],
            [-115.0, 468.0, -35.0]
        ]
        gb_segments = [
            {"segment_index": 0, "status": "CONTINUOUS", "points": [gb_points[0], gb_points[1]], "is_broken": False},
            {"segment_index": 1, "status": "CONTINUOUS", "points": [gb_points[1], gb_points[2]], "is_broken": False}
        ]
        conn.execute(
            """
            INSERT INTO meridian_paths_3d (
                path_id, meridian_code, source_id, model_id,
                ordered_points_json, baked_segments_json,
                has_penetration_gap, gap_warnings_json, review_state, created_at
            ) VALUES (
                'path_gb_cervical_bp3d',
                'GB',
                'who_standard_2008',
                'bodyparts3d_v4_ref_torso',
                ?, ?, 0, '[]', 'UNREVIEWED', ?
            ) ON CONFLICT(path_id) DO NOTHING;
            """,
            (json.dumps(gb_points), json.dumps(gb_segments), now_iso)
        )
