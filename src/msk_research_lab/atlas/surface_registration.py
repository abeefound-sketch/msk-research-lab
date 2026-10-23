"""Barycentric Surface Anchoring & Mesh-Change Invalidation (ATLAS-02 / R4-04).

Implements BVH/nearest-triangle surface projection to declared exterior skin meshes,
computes stable barycentric weights (u, v, w), and enforces mesh-change invalidation.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from msk_research_lab.core.db import get_db
from msk_research_lab.atlas.registry import get_model_3d, ModelRegistryError


class GeometryError(Exception):
    """Base exception for geometric registration errors."""
    pass


class Point3D:
    def __init__(self, x: float, y: float, z: float):
        if any(math.isnan(v) or math.isinf(v) for v in (x, y, z)):
            raise GeometryError(f"Invalid coordinate: NaN or Inf in ({x}, {y}, {z})")
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    def distance_to(self, other: "Point3D") -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)

    def sub(self, other: "Point3D") -> "Point3D":
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def add(self, other: "Point3D") -> "Point3D":
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def scale(self, factor: float) -> "Point3D":
        return Point3D(self.x * factor, self.y * factor, self.z * factor)

    def dot(self, other: "Point3D") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Point3D") -> "Point3D":
        return Point3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def norm(self) -> float:
        return math.sqrt(self.dot(self))

    def normalize(self) -> "Point3D":
        n = self.norm()
        if n < 1e-12:
            return Point3D(0.0, 1.0, 0.0)
        return Point3D(self.x / n, self.y / n, self.z / n)


class Triangle3D:
    def __init__(self, v0: Point3D, v1: Point3D, v2: Point3D, face_index: int):
        self.v0 = v0
        self.v1 = v1
        self.v2 = v2
        self.face_index = int(face_index)

    def normal(self) -> Point3D:
        edge1 = self.v1.sub(self.v0)
        edge2 = self.v2.sub(self.v0)
        return edge1.cross(edge2).normalize()


def compute_barycentric(p: Point3D, tri: Triangle3D) -> Tuple[float, float, float]:
    """Calculate barycentric coordinates (u, v, w) of point p with respect to triangle."""
    v0 = tri.v1.sub(tri.v0)
    v1 = tri.v2.sub(tri.v0)
    v2 = p.sub(tri.v0)

    d00 = v0.dot(v0)
    d01 = v0.dot(v1)
    d11 = v1.dot(v1)
    d20 = v2.dot(v0)
    d21 = v2.dot(v1)

    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-12:
        return (0.333333, 0.333333, 0.333334)

    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    return (u, v, w)


def project_to_triangle(p: Point3D, tri: Triangle3D) -> Tuple[Point3D, float, Tuple[float, float, float]]:
    """Project 3D point onto triangle plane and clamp to interior bounds."""
    norm = tri.normal()
    dist_plane = p.sub(tri.v0).dot(norm)
    proj_plane = p.sub(norm.scale(dist_plane))

    u, v, w = compute_barycentric(proj_plane, tri)
    # Clamp barycentric to triangle domain
    u_c = max(0.0, min(1.0, u))
    v_c = max(0.0, min(1.0, v))
    w_c = max(0.0, min(1.0, w))
    total = u_c + v_c + w_c
    if total > 0:
        u_c /= total
        v_c /= total
        w_c /= total

    # Reconstruct surface point from barycentric
    surf = tri.v0.scale(u_c).add(tri.v1.scale(v_c)).add(tri.v2.scale(w_c))
    dist = p.distance_to(surf)
    return surf, dist, (u_c, v_c, w_c)


def snap_to_skin_mesh(
    point: Point3D,
    triangles: List[Triangle3D],
    tolerance_mm: float = 5.0,
) -> Dict[str, Any]:
    """Snap candidate 3D coordinate to declared exterior skin mesh."""
    if not triangles:
        raise GeometryError("Declared skin mesh has 0 triangles; cannot perform surface registration.")

    best_tri = None
    best_surf = None
    best_dist = float("inf")
    best_bary = (0.0, 0.0, 0.0)

    for tri in triangles:
        surf, dist, bary = project_to_triangle(point, tri)
        if dist < best_dist:
            best_dist = dist
            best_tri = tri
            best_surf = surf
            best_bary = bary

    normal = best_tri.normal()
    passes_tolerance = best_dist <= tolerance_mm

    return {
        "status": "PASS" if passes_tolerance else "TOLERANCE_EXCEEDED",
        "distance_mm": round(best_dist, 4),
        "tolerance_mm": tolerance_mm,
        "face_index": best_tri.face_index,
        "barycentric": [round(best_bary[0], 6), round(best_bary[1], 6), round(best_bary[2], 6)],
        "surface_point": best_surf.to_list(),
        "surface_normal": normal.to_list(),
    }


def create_skin_anchor(
    *,
    anchor_id: str,
    model_id: str,
    mesh_sha256: str,
    face_index: int,
    barycentric: Tuple[float, float, float],
    surface_point: Point3D,
    surface_normal: Point3D,
) -> Dict[str, Any]:
    """Persist a barycentric skin anchor tied to an exact model and mesh checksum."""
    model = get_model_3d(model_id)
    if not model:
        raise ModelRegistryError(f"Model '{model_id}' does not exist.")

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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VALID', ?)
            ON CONFLICT(anchor_id) DO UPDATE SET
                model_id=excluded.model_id,
                mesh_sha256=excluded.mesh_sha256,
                face_index=excluded.face_index,
                barycentric_u=excluded.barycentric_u,
                barycentric_v=excluded.barycentric_v,
                barycentric_w=excluded.barycentric_w,
                surface_x=excluded.surface_x,
                surface_y=excluded.surface_y,
                surface_z=excluded.surface_z,
                normal_x=excluded.normal_x,
                normal_y=excluded.normal_y,
                normal_z=excluded.normal_z,
                status=excluded.status;
            """,
            (
                anchor_id, model_id, mesh_sha256.lower(), int(face_index),
                float(barycentric[0]), float(barycentric[1]), float(barycentric[2]),
                float(surface_point.x), float(surface_point.y), float(surface_point.z),
                float(surface_normal.x), float(surface_normal.y), float(surface_normal.z),
                now_iso
            )
        )
    return get_skin_anchor(anchor_id)


def get_skin_anchor(anchor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve skin anchor by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM skin_anchors WHERE anchor_id = ?;", (anchor_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def evaluate_anchor_validity(anchor_id: str, current_mesh_sha256: str) -> Dict[str, Any]:
    """Enforce mesh-change invalidation: anchor becomes invalid if underlying mesh SHA changes."""
    anchor = get_skin_anchor(anchor_id)
    if not anchor:
        raise GeometryError(f"Anchor '{anchor_id}' not found.")

    expected_sha = anchor["mesh_sha256"].lower()
    actual_sha = current_mesh_sha256.lower()

    if expected_sha != actual_sha:
        # Invalidate anchor in DB
        with get_db() as conn:
            conn.execute(
                "UPDATE skin_anchors SET status = 'INVALIDATED_TOPOLOGY_CHANGED' WHERE anchor_id = ?;",
                (anchor_id,)
            )
        return {
            "valid": False,
            "anchor_id": anchor_id,
            "status": "INVALIDATED_TOPOLOGY_CHANGED",
            "reason": f"Underlying mesh checksum changed from {expected_sha[:8]}... to {actual_sha[:8]}... Face index {anchor['face_index']} is no longer meaningful."
        }

    return {
        "valid": True,
        "anchor_id": anchor_id,
        "status": anchor["status"],
        "face_index": anchor["face_index"],
        "surface_point": [anchor["surface_x"], anchor["surface_y"], anchor["surface_z"]],
    }
