"""Unit tests for Two-Source 3D Comparison Guard (ATLAS-03 / R4-06)."""

import pytest
from msk_research_lab.atlas.comparisons import compare_placements_3d


def test_comparison_unregistered_different_models_blocked():
    """Unregistered sources with different base models prohibit fake millimeter difference."""
    placement_a = {
        "source_id": "source_tcm_3d",
        "model_id": "model_alpha",
        "frame_registered": False,
        "x": 10.0, "y": 20.0, "z": 30.0
    }
    placement_b = {
        "source_id": "source_open_anatomy",
        "model_id": "model_beta",
        "frame_registered": False,
        "x": 14.0, "y": 20.0, "z": 30.0
    }

    res = compare_placements_3d(
        point_code="GB21",
        placement_a=placement_a,
        placement_b=placement_b,
        tolerance_mm=5.0
    )

    assert res["classification"] == "NOT_COMPARABLE"
    assert res["geometric_comparability_state"] == "UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL"
    assert res["measured_distance_mm"] is None
    assert "prohibited" in res["reason"].lower()


def test_comparison_registered_common_frame_match():
    """Two placements in common registered frame within tolerance classify as MATCH."""
    placement_a = {
        "source_id": "source_who_2008",
        "model_id": "bodyparts3d_v4_ref_torso",
        "frame_registered": True,
        "x": -97.5, "y": 475.0, "z": -45.0
    }
    placement_b = {
        "source_id": "source_nam_2015",
        "model_id": "bodyparts3d_v4_ref_torso",
        "frame_registered": True,
        "x": -98.0, "y": 476.0, "z": -45.5
    }

    res = compare_placements_3d(
        point_code="GB21",
        placement_a=placement_a,
        placement_b=placement_b,
        tolerance_mm=5.0
    )

    assert res["classification"] == "MATCH"
    assert res["geometric_comparability_state"] == "REGISTERED_COMMON_FRAME"
    assert res["measured_distance_mm"] is not None
    assert res["measured_distance_mm"] <= 5.0
    assert "displacement_vector" in res
    assert "dx" in res["displacement_vector"]


def test_comparison_registered_common_frame_difference():
    """Two placements in common registered frame beyond tolerance classify as DIFFERENCE."""
    placement_a = {
        "source_id": "source_school_a",
        "model_id": "bodyparts3d_v4_ref_torso",
        "frame_registered": True,
        "x": -97.5, "y": 475.0, "z": -45.0
    }
    placement_b = {
        "source_id": "source_school_b",
        "model_id": "bodyparts3d_v4_ref_torso",
        "frame_registered": True,
        "x": -97.5, "y": 490.0, "z": -45.0 # 15 mm shift in Y
    }

    res = compare_placements_3d(
        point_code="GB21",
        placement_a=placement_a,
        placement_b=placement_b,
        tolerance_mm=5.0
    )

    assert res["classification"] == "DIFFERENCE"
    assert res["geometric_comparability_state"] == "REGISTERED_COMMON_FRAME"
    assert res["measured_distance_mm"] == pytest.approx(15.0, abs=0.1)
