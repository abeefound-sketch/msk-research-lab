"""Unit tests for Barycentric Surface Registration & Invalidation (ATLAS-02 / R4-04)."""

import pytest
from msk_research_lab.atlas.surface_registration import (
    Point3D, Triangle3D, compute_barycentric, project_to_triangle,
    snap_to_skin_mesh, create_skin_anchor, get_skin_anchor,
    evaluate_anchor_validity, GeometryError
)
from msk_research_lab.atlas.registry import seed_standard_models_if_empty, ModelRegistryError


def test_barycentric_projection_exact_vertex():
    v0 = Point3D(0.0, 0.0, 0.0)
    v1 = Point3D(10.0, 0.0, 0.0)
    v2 = Point3D(0.0, 10.0, 0.0)
    tri = Triangle3D(v0, v1, v2, face_index=0)

    # Point directly on v0
    surf, dist, bary = project_to_triangle(v0, tri)
    assert dist == 0.0
    assert abs(bary[0] - 1.0) < 1e-4
    assert abs(bary[1] - 0.0) < 1e-4
    assert abs(bary[2] - 0.0) < 1e-4


def test_barycentric_projection_center():
    v0 = Point3D(0.0, 0.0, 0.0)
    v1 = Point3D(10.0, 0.0, 0.0)
    v2 = Point3D(0.0, 10.0, 0.0)
    tri = Triangle3D(v0, v1, v2, face_index=1)

    # Centroid of triangle
    centroid = Point3D(10.0 / 3.0, 10.0 / 3.0, 0.0)
    surf, dist, bary = project_to_triangle(centroid, tri)
    assert dist == pytest.approx(0.0, abs=1e-4)
    assert bary[0] == pytest.approx(1.0 / 3.0, abs=1e-4)
    assert bary[1] == pytest.approx(1.0 / 3.0, abs=1e-4)
    assert bary[2] == pytest.approx(1.0 / 3.0, abs=1e-4)


def test_snap_to_skin_mesh_within_tolerance():
    tri = Triangle3D(
        Point3D(0.0, 0.0, 0.0),
        Point3D(100.0, 0.0, 0.0),
        Point3D(0.0, 100.0, 0.0),
        face_index=42
    )
    # Point 2 mm above triangle surface
    p = Point3D(20.0, 20.0, 2.0)
    res = snap_to_skin_mesh(p, [tri], tolerance_mm=5.0)

    assert res["status"] == "PASS"
    assert res["distance_mm"] == pytest.approx(2.0, abs=0.01)
    assert res["face_index"] == 42
    assert res["surface_point"] == [20.0, 20.0, 0.0]


def test_snap_to_skin_mesh_exceeds_tolerance():
    tri = Triangle3D(
        Point3D(0.0, 0.0, 0.0),
        Point3D(100.0, 0.0, 0.0),
        Point3D(0.0, 100.0, 0.0),
        face_index=42
    )
    # Point 8 mm away (tolerance 5 mm)
    p = Point3D(20.0, 20.0, 8.0)
    res = snap_to_skin_mesh(p, [tri], tolerance_mm=5.0)

    assert res["status"] == "TOLERANCE_EXCEEDED"
    assert res["distance_mm"] == pytest.approx(8.0, abs=0.01)


def test_snap_to_skin_empty_triangles():
    with pytest.raises(GeometryError, match="0 triangles"):
        snap_to_skin_mesh(Point3D(0, 0, 0), [], tolerance_mm=5.0)


def test_create_and_invalidate_skin_anchor():
    seed_standard_models_if_empty()

    original_sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    anchor = create_skin_anchor(
        anchor_id="anchor_test_shoulder_01",
        model_id="bodyparts3d_v4_ref_torso",
        mesh_sha256=original_sha,
        face_index=105,
        barycentric=(0.25, 0.25, 0.50),
        surface_point=Point3D(-50.0, 480.0, -30.0),
        surface_normal=Point3D(0.0, 1.0, 0.0)
    )
    assert anchor["anchor_id"] == "anchor_test_shoulder_01"
    assert anchor["status"] == "VALID"

    # Evaluation with same SHA: valid
    eval_same = evaluate_anchor_validity("anchor_test_shoulder_01", original_sha)
    assert eval_same["valid"] is True
    assert eval_same["status"] == "VALID"

    # Evaluation with changed SHA: INVALIDATED_TOPOLOGY_CHANGED
    changed_sha = "f" * 64
    eval_diff = evaluate_anchor_validity("anchor_test_shoulder_01", changed_sha)
    assert eval_diff["valid"] is False
    assert eval_diff["status"] == "INVALIDATED_TOPOLOGY_CHANGED"
    assert "Topology" in eval_diff["reason"] or "topology" in eval_diff["reason"] or "checksum" in eval_diff["reason"]
