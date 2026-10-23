"""Private Atlas Project Management & Namespaces (ATLAS-05 / R5-01).

Guarantees isolation of researcher draft atlases, prevents namespace collisions
with standard FMA anatomy or canonical WHO concepts, and maintains project versioning.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from msk_research_lab.core.db import get_db


ALLOWED_NAMESPACES = {
    "DIEN_CHAN",
    "TCM",
    "THAI_SEN",
    "TRIGGER_POINT",
    "MANUAL_THERAPY",
    "CUSTOM_RESEARCH"
}

FORBIDDEN_CONCEPT_PREFIXES = {
    "FMA:", "FMA_", "ANATOMY:", "UBERON:", "CL:"
}


class StudioProjectError(Exception):
    """Exception raised for private studio project violations."""
    pass


def create_project(
    *,
    project_id: str,
    title: str,
    namespace: str,
    description: Optional[str] = None,
    base_model_id: Optional[str] = None,
    base_image_sha256: Optional[str] = None,
    license: str = "PROPRIETARY_DRAFT",
) -> Dict[str, Any]:
    """Create a private research atlas project."""
    clean_id = project_id.strip()
    clean_ns = namespace.strip().upper()

    if not clean_id:
        raise StudioProjectError("Project ID cannot be empty.")

    if clean_ns not in ALLOWED_NAMESPACES:
        raise StudioProjectError(
            f"Invalid namespace '{namespace}'. Must be one of {sorted(ALLOWED_NAMESPACES)}."
        )

    # Collision guard: project ID cannot hijack formal anatomy namespaces
    for prefix in FORBIDDEN_CONCEPT_PREFIXES:
        if clean_id.upper().startswith(prefix):
            raise StudioProjectError(
                f"Project ID '{clean_id}' violates namespace boundary: formal anatomy namespace '{prefix}' is reserved."
            )

    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO private_atlas_projects (
                project_id, title, namespace, description, base_model_id,
                base_image_sha256, license, version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                title=excluded.title,
                namespace=excluded.namespace,
                description=excluded.description,
                base_model_id=excluded.base_model_id,
                base_image_sha256=excluded.base_image_sha256,
                license=excluded.license,
                updated_at=excluded.updated_at;
            """,
            (
                clean_id, title.strip(), clean_ns, description,
                base_model_id, base_image_sha256, license, now_iso, now_iso
            )
        )

    return get_project(clean_id)


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve private project metadata with point count."""
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM studio_points WHERE project_id = p.project_id AND is_deleted = 0) as active_point_count,
                   (SELECT COUNT(*) FROM studio_edit_history WHERE project_id = p.project_id) as history_count
            FROM private_atlas_projects p
            WHERE p.project_id = ?;
            """,
            (project_id.strip(),)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_projects() -> List[Dict[str, Any]]:
    """List all private studio projects."""
    with get_db() as conn:
        cur = conn.execute(
            """
            SELECT p.*,
                   (SELECT COUNT(*) FROM studio_points WHERE project_id = p.project_id AND is_deleted = 0) as active_point_count
            FROM private_atlas_projects p
            ORDER BY p.updated_at DESC;
            """
        )
        return [dict(r) for r in cur.fetchall()]


def bump_project_version(project_id: str) -> int:
    """Increment project version upon milestone save."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE private_atlas_projects
            SET version = version + 1, updated_at = ?
            WHERE project_id = ?;
            """,
            (now_iso, project_id.strip())
        )
        cur = conn.execute("SELECT version FROM private_atlas_projects WHERE project_id = ?;", (project_id.strip(),))
        row = cur.fetchone()
        if not row:
            raise StudioProjectError(f"Project '{project_id}' not found.")
        return row["version"]
