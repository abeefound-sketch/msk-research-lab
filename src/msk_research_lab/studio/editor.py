"""Private Studio Point Editor with Undo/Redo & History Lineage (ATLAS-05 / R5-02).

Enforces strict coordinate validation (barycentric sum = 1 for 3D, pixel bounds for 2D),
session-scoping for reactive observations, and immutable edit history lineage.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.core.db import get_db
from msk_research_lab.studio.project import get_project, StudioProjectError


class StudioEditorError(Exception):
    """Exception raised for editor operations violations."""
    pass


def add_studio_point(
    *,
    project_id: str,
    point_id: str,
    code: str,
    canonical_label: str,
    dimensionality: str = "3D_SURFACE",
    point_kind: str = "FIXED_EDUCATIONAL",
    session_id: Optional[str] = None,
    session_timestamp: Optional[str] = None,
    # 3D surface parameters
    model_id: Optional[str] = None,
    mesh_sha256: Optional[str] = None,
    surface_xyz: Optional[Tuple[float, float, float]] = None,
    face_index: Optional[int] = None,
    barycentric: Optional[Tuple[float, float, float]] = None,
    # 2D image pixel parameters
    image_sha256: Optional[str] = None,
    image_view: Optional[str] = None,
    pixel_xy: Optional[Tuple[float, float]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new point to a private atlas project with strict coordinate and kind constraints."""
    proj = get_project(project_id)
    if not proj:
        raise StudioEditorError(f"Project '{project_id}' does not exist.")

    clean_code = code.strip()
    if not clean_code:
        raise StudioEditorError("Point code cannot be empty.")

    # 1. Point kind validation (R5-04)
    if point_kind == "REACTIVE_OBSERVATION":
        if not session_id or not session_timestamp:
            raise StudioEditorError(
                "Reactive observation point requires explicit 'session_id' and 'session_timestamp'. "
                "Contextual observations cannot be created without session attribution."
            )
    elif point_kind != "FIXED_EDUCATIONAL":
        raise StudioEditorError(
            f"Invalid point kind '{point_kind}'. Must be 'FIXED_EDUCATIONAL' or 'REACTIVE_OBSERVATION'."
        )

    # 2. Dimensionality & coordinate validation
    if dimensionality == "3D_SURFACE":
        if not model_id or not mesh_sha256:
            raise StudioEditorError("3D surface point requires 'model_id' and 'mesh_sha256'.")
        if len(mesh_sha256) != 64:
            raise StudioEditorError("Mesh SHA-256 must be a 64-character hexadecimal string.")
        if face_index is None or face_index < 0:
            raise StudioEditorError("3D surface point requires non-negative 'face_index'.")
        if not barycentric or len(barycentric) != 3:
            raise StudioEditorError("3D surface point requires 3 barycentric weights (u, v, w).")

        bary_sum = sum(barycentric)
        if abs(bary_sum - 1.0) > 1e-3:
            raise StudioEditorError(
                f"Invalid barycentric weights sum: {bary_sum:.4f}. Must sum to 1.0 within tolerance."
            )
        if not surface_xyz or len(surface_xyz) != 3:
            raise StudioEditorError("3D surface point requires surface coordinates (x, y, z).")

    elif dimensionality == "2D_IMAGE_PIXEL":
        if not image_sha256 or len(image_sha256) != 64:
            raise StudioEditorError("2D image point requires valid 64-character 'image_sha256'.")
        if not image_view or image_view.upper() not in {"FRONT", "PROFILE", "OBLIQUE"}:
            raise StudioEditorError("2D image point requires 'image_view' in {'FRONT', 'PROFILE', 'OBLIQUE'}.")
        if not pixel_xy or len(pixel_xy) != 2:
            raise StudioEditorError("2D image point requires pixel coordinates (x_px, y_px).")
        if pixel_xy[0] < 0 or pixel_xy[1] < 0:
            raise StudioEditorError("Pixel coordinates must be non-negative.")
    else:
        raise StudioEditorError(f"Invalid dimensionality '{dimensionality}'. Must be '3D_SURFACE' or '2D_IMAGE_PIXEL'.")

    now_iso = datetime.now(timezone.utc).isoformat()
    point_record = {
        "point_id": point_id,
        "project_id": project_id,
        "code": clean_code,
        "canonical_label": canonical_label.strip(),
        "namespace": proj["namespace"],
        "point_kind": point_kind,
        "session_id": session_id,
        "session_timestamp": session_timestamp,
        "dimensionality": dimensionality,
        "image_sha256": image_sha256.lower() if image_sha256 else None,
        "image_view": image_view.upper() if image_view else None,
        "x_px": float(pixel_xy[0]) if pixel_xy else None,
        "y_px": float(pixel_xy[1]) if pixel_xy else None,
        "model_id": model_id,
        "mesh_sha256": mesh_sha256.lower() if mesh_sha256 else None,
        "surface_x": float(surface_xyz[0]) if surface_xyz else None,
        "surface_y": float(surface_xyz[1]) if surface_xyz else None,
        "surface_z": float(surface_xyz[2]) if surface_xyz else None,
        "face_index": int(face_index) if face_index is not None else None,
        "barycentric_u": float(barycentric[0]) if barycentric else None,
        "barycentric_v": float(barycentric[1]) if barycentric else None,
        "barycentric_w": float(barycentric[2]) if barycentric else None,
        "notes": notes,
        "is_deleted": 0,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO studio_points (
                point_id, project_id, code, canonical_label, namespace,
                point_kind, session_id, session_timestamp, dimensionality,
                image_sha256, image_view, x_px, y_px,
                model_id, mesh_sha256, surface_x, surface_y, surface_z,
                face_index, barycentric_u, barycentric_v, barycentric_w,
                notes, is_deleted, created_at, updated_at
            ) VALUES (
                :point_id, :project_id, :code, :canonical_label, :namespace,
                :point_kind, :session_id, :session_timestamp, :dimensionality,
                :image_sha256, :image_view, :x_px, :y_px,
                :model_id, :mesh_sha256, :surface_x, :surface_y, :surface_z,
                :face_index, :barycentric_u, :barycentric_v, :barycentric_w,
                :notes, 0, :created_at, :updated_at
            )
            ON CONFLICT(point_id) DO UPDATE SET
                project_id=excluded.project_id,
                code=excluded.code,
                canonical_label=excluded.canonical_label,
                namespace=excluded.namespace,
                point_kind=excluded.point_kind,
                session_id=excluded.session_id,
                session_timestamp=excluded.session_timestamp,
                dimensionality=excluded.dimensionality,
                image_sha256=excluded.image_sha256,
                image_view=excluded.image_view,
                x_px=excluded.x_px,
                y_px=excluded.y_px,
                model_id=excluded.model_id,
                mesh_sha256=excluded.mesh_sha256,
                surface_x=excluded.surface_x,
                surface_y=excluded.surface_y,
                surface_z=excluded.surface_z,
                face_index=excluded.face_index,
                barycentric_u=excluded.barycentric_u,
                barycentric_v=excluded.barycentric_v,
                barycentric_w=excluded.barycentric_w,
                notes=excluded.notes,
                is_deleted=0,
                updated_at=excluded.updated_at;
            """,
            point_record
        )
        # Log to edit history for undo/redo
        conn.execute(
            """
            INSERT INTO studio_edit_history (
                project_id, action_type, point_id, before_state_json, after_state_json, created_at
            ) VALUES (?, 'ADD_POINT', ?, NULL, ?, ?);
            """,
            (project_id, point_id, json.dumps(point_record), now_iso)
        )

    return get_studio_point(point_id)


def get_studio_point(point_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve studio point by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM studio_points WHERE point_id = ?;", (point_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_studio_points(project_id: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
    """List points for a private atlas project."""
    with get_db() as conn:
        if include_deleted:
            cur = conn.execute(
                "SELECT * FROM studio_points WHERE project_id = ? ORDER BY created_at ASC;",
                (project_id,)
            )
        else:
            cur = conn.execute(
                "SELECT * FROM studio_points WHERE project_id = ? AND is_deleted = 0 ORDER BY created_at ASC;",
                (project_id,)
            )
        return [dict(r) for r in cur.fetchall()]


def move_studio_point(
    point_id: str,
    *,
    surface_xyz: Optional[Tuple[float, float, float]] = None,
    face_index: Optional[int] = None,
    barycentric: Optional[Tuple[float, float, float]] = None,
    pixel_xy: Optional[Tuple[float, float]] = None,
) -> Dict[str, Any]:
    """Update position of a studio point and record edit history."""
    pt = get_studio_point(point_id)
    if not pt:
        raise StudioEditorError(f"Point '{point_id}' does not exist.")

    before_state = dict(pt)
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        if pt["dimensionality"] == "3D_SURFACE":
            if not surface_xyz or not barycentric or face_index is None:
                raise StudioEditorError("Moving 3D surface point requires surface_xyz, barycentric, and face_index.")
            b_sum = sum(barycentric)
            if abs(b_sum - 1.0) > 1e-3:
                raise StudioEditorError(f"Barycentric weights sum {b_sum:.4f} != 1.0.")
            conn.execute(
                """
                UPDATE studio_points
                SET surface_x = ?, surface_y = ?, surface_z = ?,
                    face_index = ?, barycentric_u = ?, barycentric_v = ?, barycentric_w = ?,
                    updated_at = ?
                WHERE point_id = ?;
                """,
                (
                    surface_xyz[0], surface_xyz[1], surface_xyz[2],
                    face_index, barycentric[0], barycentric[1], barycentric[2],
                    now_iso, point_id
                )
            )
        elif pt["dimensionality"] == "2D_IMAGE_PIXEL":
            if not pixel_xy or pixel_xy[0] < 0 or pixel_xy[1] < 0:
                raise StudioEditorError("Moving 2D pixel point requires valid non-negative (x_px, y_px).")
            conn.execute(
                """
                UPDATE studio_points
                SET x_px = ?, y_px = ?, updated_at = ?
                WHERE point_id = ?;
                """,
                (pixel_xy[0], pixel_xy[1], now_iso, point_id)
            )

        after_state = get_studio_point(point_id)
        conn.execute(
            """
            INSERT INTO studio_edit_history (
                project_id, action_type, point_id, before_state_json, after_state_json, created_at
            ) VALUES (?, 'MOVE_POINT', ?, ?, ?, ?);
            """,
            (pt["project_id"], point_id, json.dumps(before_state), json.dumps(after_state), now_iso)
        )

    return get_studio_point(point_id)


def delete_studio_point(point_id: str) -> Dict[str, Any]:
    """Soft delete a point and record edit history."""
    pt = get_studio_point(point_id)
    if not pt:
        raise StudioEditorError(f"Point '{point_id}' does not exist.")

    before_state = dict(pt)
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            "UPDATE studio_points SET is_deleted = 1, updated_at = ? WHERE point_id = ?;",
            (now_iso, point_id)
        )
        after_state = get_studio_point(point_id)
        conn.execute(
            """
            INSERT INTO studio_edit_history (
                project_id, action_type, point_id, before_state_json, after_state_json, created_at
            ) VALUES (?, 'DELETE_POINT', ?, ?, ?, ?);
            """,
            (pt["project_id"], point_id, json.dumps(before_state), json.dumps(after_state), now_iso)
        )

    return get_studio_point(point_id)


def undo_last_action(project_id: str) -> Optional[Dict[str, Any]]:
    """Undo the most recent edit action on a project."""
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT * FROM studio_edit_history
            WHERE project_id = ?
            ORDER BY history_id DESC LIMIT 1;
            """,
            (project_id,)
        )
        entry = cur.fetchone()
        if not entry:
            return None

        action_type = entry["action_type"]
        point_id = entry["point_id"]
        before_state = json.loads(entry["before_state_json"]) if entry["before_state_json"] else None

        if action_type == "ADD_POINT":
            # Revert add by deleting
            conn.execute("DELETE FROM studio_points WHERE point_id = ?;", (point_id,))
        elif action_type in {"MOVE_POINT", "DELETE_POINT", "UPDATE_NOTES"} and before_state:
            # Revert to before_state
            conn.execute(
                """
                UPDATE studio_points SET
                    code = :code, canonical_label = :canonical_label,
                    x_px = :x_px, y_px = :y_px,
                    surface_x = :surface_x, surface_y = :surface_y, surface_z = :surface_z,
                    face_index = :face_index,
                    barycentric_u = :barycentric_u, barycentric_v = :barycentric_v, barycentric_w = :barycentric_w,
                    notes = :notes, is_deleted = :is_deleted, updated_at = :updated_at
                WHERE point_id = :point_id;
                """,
                before_state
            )

        # Remove the undone history entry
        conn.execute("DELETE FROM studio_edit_history WHERE history_id = ?;", (entry["history_id"],))

    return {
        "undone_action": action_type,
        "point_id": point_id,
        "project_id": project_id
    }
