"""Versioned Studio Export, Import, Validation & Diff (ATLAS-05 / R5-05).

Provides roundtrip serialization conforming to schemas/atlas_point.schema.json,
enforces rights and topological integrity on import, and computes draft diffs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.core.db import get_db
from msk_research_lab.studio.project import get_project, create_project, bump_project_version, StudioProjectError
from msk_research_lab.studio.editor import list_studio_points, add_studio_point, StudioEditorError


FORBIDDEN_TRANSFER_LICENSES = {
    "UNREVIEWED_PROPRIETARY",
    "UNKNOWN_RIGHTS",
    "PIRATED_COPY",
    "REVOKED"
}


class TransferError(Exception):
    """Exception raised for studio package transfer and schema errors."""
    pass


def export_studio_project(project_id: str) -> Dict[str, Any]:
    """Export private atlas project as a versioned JSON bundle."""
    proj = get_project(project_id)
    if not proj:
        raise TransferError(f"Project '{project_id}' not found.")

    points = list_studio_points(project_id, include_deleted=False)
    now_iso = datetime.now(timezone.utc).isoformat()

    # License check
    if proj.get("license") in FORBIDDEN_TRANSFER_LICENSES:
        raise TransferError(
            f"Cannot export project with forbidden/unreviewed license: '{proj.get('license')}'."
        )

    export_payload = {
        "schema_version": "3.0.0",
        "exported_at": now_iso,
        "project": {
            "project_id": proj["project_id"],
            "title": proj["title"],
            "namespace": proj["namespace"],
            "description": proj["description"],
            "base_model_id": proj["base_model_id"],
            "base_image_sha256": proj["base_image_sha256"],
            "license": proj["license"],
            "version": proj["version"],
        },
        "points": points,
    }

    # Content digest
    points_bytes = json.dumps(points, sort_keys=True).encode("utf-8")
    export_payload["points_sha256"] = hashlib.sha256(points_bytes).hexdigest()

    return export_payload


def validate_studio_import_payload(payload: Dict[str, Any]) -> None:
    """Validate import payload schema, licenses, and geometric invariants."""
    if not isinstance(payload, dict):
        raise TransferError("Import payload must be a JSON object.")

    if payload.get("schema_version") != "3.0.0":
        raise TransferError(
            f"Unsupported schema version '{payload.get('schema_version')}'. Expected '3.0.0'."
        )

    proj_meta = payload.get("project")
    if not proj_meta or not isinstance(proj_meta, dict):
        raise TransferError("Import payload missing 'project' metadata object.")

    # License validation
    license_str = proj_meta.get("license", "")
    if license_str in FORBIDDEN_TRANSFER_LICENSES:
        raise TransferError(f"Import rejected: License '{license_str}' is forbidden or revoked.")

    points = payload.get("points")
    if not isinstance(points, list):
        raise TransferError("Import payload missing 'points' array.")

    # Topological & geometric validation for each point
    for idx, pt in enumerate(points):
        code = pt.get("code")
        if not code:
            raise TransferError(f"Point at index {idx} is missing 'code'.")

        dim = pt.get("dimensionality")
        if dim == "3D_SURFACE":
            u = pt.get("barycentric_u")
            v = pt.get("barycentric_v")
            w = pt.get("barycentric_w")
            if any(x is None for x in (u, v, w)):
                raise TransferError(f"Point '{code}' has missing barycentric weights.")
            b_sum = u + v + w
            if abs(b_sum - 1.0) > 1e-3:
                raise TransferError(
                    f"Point '{code}' has corrupt barycentric coordinates sum {b_sum:.4f} != 1.0."
                )
            if not pt.get("mesh_sha256") or len(pt["mesh_sha256"]) != 64:
                raise TransferError(f"Point '{code}' has invalid mesh SHA-256 digest.")
        elif dim == "2D_IMAGE_PIXEL":
            if pt.get("x_px") is None or pt.get("y_px") is None:
                raise TransferError(f"Point '{code}' has missing pixel coordinates.")
            if pt["x_px"] < 0 or pt["y_px"] < 0:
                raise TransferError(f"Point '{code}' has negative pixel coordinates.")
            if not pt.get("image_sha256") or len(pt["image_sha256"]) != 64:
                raise TransferError(f"Point '{code}' has invalid image SHA-256 digest.")
        else:
            raise TransferError(f"Point '{code}' has unknown dimensionality '{dim}'.")


def import_studio_project(payload: Dict[str, Any], overwrite_existing: bool = False) -> Dict[str, Any]:
    """Import and persist a validated private studio package."""
    validate_studio_import_payload(payload)

    proj_meta = payload["project"]
    proj_id = proj_meta["project_id"]

    existing = get_project(proj_id)
    if existing and not overwrite_existing:
        raise TransferError(f"Project '{proj_id}' already exists. Specify overwrite=True to replace.")

    # Create or update project
    create_project(
        project_id=proj_id,
        title=proj_meta["title"],
        namespace=proj_meta["namespace"],
        description=proj_meta.get("description"),
        base_model_id=proj_meta.get("base_model_id"),
        base_image_sha256=proj_meta.get("base_image_sha256"),
        license=proj_meta.get("license", "PROPRIETARY_DRAFT"),
    )

    imported_points = []
    for pt in payload["points"]:
        pt_rec = add_studio_point(
            project_id=proj_id,
            point_id=pt["point_id"],
            code=pt["code"],
            canonical_label=pt["canonical_label"],
            dimensionality=pt["dimensionality"],
            point_kind=pt.get("point_kind", "FIXED_EDUCATIONAL"),
            session_id=pt.get("session_id"),
            session_timestamp=pt.get("session_timestamp"),
            model_id=pt.get("model_id"),
            mesh_sha256=pt.get("mesh_sha256"),
            surface_xyz=(pt["surface_x"], pt["surface_y"], pt["surface_z"]) if pt.get("surface_x") is not None else None,
            face_index=pt.get("face_index"),
            barycentric=(pt["barycentric_u"], pt["barycentric_v"], pt["barycentric_w"]) if pt.get("barycentric_u") is not None else None,
            image_sha256=pt.get("image_sha256"),
            image_view=pt.get("image_view"),
            pixel_xy=(pt["x_px"], pt["y_px"]) if pt.get("x_px") is not None else None,
            notes=pt.get("notes")
        )
        imported_points.append(pt_rec)

    return {
        "status": "IMPORTED",
        "project_id": proj_id,
        "imported_point_count": len(imported_points),
    }


def compute_project_diff(project_id: str, comparison_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compute geometric and metadata differences between current project state and comparison bundle."""
    current_points = {p["code"]: p for p in list_studio_points(project_id, include_deleted=False)}
    comp_points = {p["code"]: p for p in comparison_payload.get("points", [])}

    added = []
    removed = []
    modified = []
    identical = []

    for code, p in comp_points.items():
        if code not in current_points:
            added.append(code)
        else:
            curr = current_points[code]
            # Check coordinate differences
            diffs = {}
            if curr["dimensionality"] == "3D_SURFACE":
                for coord in ["surface_x", "surface_y", "surface_z", "face_index"]:
                    if curr.get(coord) != p.get(coord):
                        diffs[coord] = {"current": curr.get(coord), "comparison": p.get(coord)}
            elif curr["dimensionality"] == "2D_IMAGE_PIXEL":
                for coord in ["x_px", "y_px"]:
                    if curr.get(coord) != p.get(coord):
                        diffs[coord] = {"current": curr.get(coord), "comparison": p.get(coord)}

            if diffs:
                modified.append({"code": code, "differences": diffs})
            else:
                identical.append(code)

    for code in current_points:
        if code not in comp_points:
            removed.append(code)

    return {
        "project_id": project_id,
        "added_codes": added,
        "removed_codes": removed,
        "modified_points": modified,
        "identical_codes": identical,
        "total_diff_count": len(added) + len(removed) + len(modified)
    }
