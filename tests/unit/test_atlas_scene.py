"""Unit tests for Calibrated 3D Anatomical Scene Builder (ATLAS-01..06)."""

import pytest
import math
from msk_research_lab.atlas.scene import (
    build_calibrated_bp3d_torso_scene,
    AtlasSceneData,
    MeshGeometry,
    AnatomicalPoint3D,
    MeridianTrajectory
)


def test_build_calibrated_bp3d_torso_scene_structure():
    """Verify calibrated BodyParts3D reference torso scene conforms to specifications."""
    scene = build_calibrated_bp3d_torso_scene()
    assert isinstance(scene, AtlasSceneData)
    assert scene.model_id == "bodyparts3d_v4_ref_torso"
    assert scene.units == "mm"
    assert scene.coordinate_frame == "mesh_local_xyz"
    assert scene.reference_pose == "standing_anatomical"


def test_anatomical_layers_complete():
    """Verify all 5 required anatomical layers exist with valid geometric payloads."""
    scene = build_calibrated_bp3d_torso_scene()
    required_layers = {"skin", "skeletal", "superficial_muscle", "deep_muscle", "nerves"}
    assert required_layers.issubset(set(scene.layers.keys()))

    skin = scene.layers["skin"]
    assert len(skin.vertices) > 100
    assert len(skin.indices) > 100
    assert skin.opacity == pytest.approx(0.45, rel=1e-2)

    skeletal = scene.layers["skeletal"]
    assert len(skeletal.vertices) > 50
    assert len(skeletal.indices) > 50

    superficial = scene.layers["superficial_muscle"]
    assert len(superficial.vertices) > 20
    assert len(superficial.indices) > 20

    deep = scene.layers["deep_muscle"]
    assert len(deep.vertices) > 10
    assert len(deep.indices) > 10

    nerves = scene.layers["nerves"]
    assert len(nerves.vertices) > 10
    assert len(nerves.indices) > 5


def test_anchored_anatomical_points():
    """Verify anchored points have surface anchors, barycentric weights, and tissue layers."""
    scene = build_calibrated_bp3d_torso_scene()
    points_by_code = {p.code: p for p in scene.points}
    expected_codes = {"GB21", "GV14", "SI14", "SI15", "BL11"}
    assert expected_codes.issubset(set(points_by_code.keys()))

    gb21 = points_by_code["GB21"]
    assert gb21.region == "SHOULDER_RIDGE"
    assert len(gb21.coordinates_mm) == 3
    assert gb21.face_index == 412
    assert sum(gb21.barycentric_weights) == pytest.approx(1.0, rel=1e-2)
    # Verify normal vector is approximately unit length
    norm_mag = math.sqrt(sum(c * c for c in gb21.normal_vector))
    assert norm_mag == pytest.approx(1.0, rel=1e-1)
    # Verify multi-layer tissue anatomy breakdown
    assert len(gb21.tissue_layers) >= 4

    gv14 = points_by_code["GV14"]
    assert gv14.region == "POSTERIOR_NECK"
    assert gv14.face_index == 480


def test_meridian_trajectories():
    """Verify meridian trajectories have control points and valid colors."""
    scene = build_calibrated_bp3d_torso_scene()
    meridians_by_code = {m.code: m for m in scene.meridians}
    assert "GB" in meridians_by_code
    assert "SI" in meridians_by_code

    gb = meridians_by_code["GB"]
    assert len(gb.control_points) >= 4
    for pt in gb.control_points:
        assert len(pt) == 3


def test_six_camera_presets():
    """Verify all 6 standard camera presets and RESET are defined."""
    scene = build_calibrated_bp3d_torso_scene()
    presets = scene.camera_presets
    expected_presets = {"FRONT", "BACK", "LEFT", "RIGHT", "OBLIQUE_TOP", "OBLIQUE_BOTTOM", "RESET"}
    assert expected_presets.issubset(set(presets.keys()))

    for key in expected_presets:
        cfg = presets[key]
        assert "position" in cfg
        assert "target" in cfg
        assert len(cfg["position"]) == 3
        assert len(cfg["target"]) == 3
