"""Unit tests for Meridian Path Baking & Multi-Camera Occlusion QA (ATLAS-02 / R4-05)."""

import pytest
from msk_research_lab.atlas.surface_registration import Point3D, Triangle3D, GeometryError
from msk_research_lab.atlas.path_baker import (
    bake_meridian_path, evaluate_six_view_occlusion, check_occlusion_for_normal
)
from msk_research_lab.atlas.registry import seed_standard_models_if_empty


def test_bake_continuous_meridian_path():
    seed_standard_models_if_empty()

    # Skin plane at z = 0
    triangles = [
        Triangle3D(Point3D(-100, -100, 0), Point3D(100, -100, 0), Point3D(100, 100, 0), face_index=1),
        Triangle3D(Point3D(-100, -100, 0), Point3D(100, 100, 0), Point3D(-100, 100, 0), face_index=2),
    ]

    # Points on/near the plane
    pts = [
        Point3D(-50, 0, 0),
        Point3D(0, 0, 0),
        Point3D(50, 0, 0),
    ]

    res = bake_meridian_path(
        path_id="path_test_continuous_01",
        meridian_code="LU",
        source_id="who_standard_2008",
        model_id="bodyparts3d_v4_ref_torso",
        control_points=pts,
        triangles=triangles,
        penetration_tolerance_mm=10.0
    )

    assert res["segment_count"] == 2
    assert res["has_penetration_gap"] is False
    assert len(res["gap_warnings"]) == 0
    for seg in res["baked_segments"]:
        assert seg["status"] == "CONTINUOUS"
        assert seg["is_broken"] is False


def test_bake_penetration_gap_breaks_continuity():
    seed_standard_models_if_empty()

    # Two skin triangles representing body surface curvature, with an interior gap
    # A straight chord between points (0, -50, 0) and (0, 50, 0) passes through an interior void where skin is at z = 40 mm
    triangles = [
        Triangle3D(Point3D(-50, -50, 0), Point3D(50, -50, 0), Point3D(0, -50, 5), face_index=1),
        Triangle3D(Point3D(-50, 50, 0), Point3D(50, 50, 0), Point3D(0, 50, 5), face_index=2),
    ]

    pts = [
        Point3D(0, -50, 0),
        Point3D(0, 50, 0)
    ]

    # If skin is absent in the middle, chord center (0, 0, 0) is ~50 mm from skin triangles
    res = bake_meridian_path(
        path_id="path_test_gap_01",
        meridian_code="ST",
        source_id="who_standard_2008",
        model_id="bodyparts3d_v4_ref_torso",
        control_points=pts,
        triangles=triangles,
        penetration_tolerance_mm=15.0
    )

    assert res["has_penetration_gap"] is True
    assert len(res["gap_warnings"]) > 0
    assert res["baked_segments"][0]["status"] == "DISCONTINUOUS_PENETRATION_GAP"
    assert res["baked_segments"][0]["is_broken"] is True


def test_six_view_occlusion_qa():
    # Normal pointing posterior and slightly superior (like upper trapezius/GB21)
    normal = Point3D(0.0, 0.7071, -0.7071).normalize()
    views = evaluate_six_view_occlusion(Point3D(0, 0, 0), normal)

    # FRONT view direction is (0, 0, 1). Normal dot (0, 0, 1) = -0.7071 <= 0 -> Occluded
    assert views["FRONT"]["occluded"] is True
    assert views["FRONT"]["visible"] is False

    # BACK view direction is (0, 0, -1). Normal dot (0, 0, -1) = +0.7071 > 0 -> Visible
    assert views["BACK"]["visible"] is True
    assert views["BACK"]["occluded"] is False

    # OBLIQUE_TOP direction has positive Y and positive Z...
    assert "OBLIQUE_TOP" in views
    assert "OBLIQUE_BOTTOM" in views
