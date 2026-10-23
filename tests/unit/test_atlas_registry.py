"""Unit tests for 3D Anatomical Model Registry (ATLAS-01..03 / R4-03)."""

import pytest
from msk_research_lab.atlas.registry import (
    register_model_3d, get_model_3d, list_models_3d,
    seed_standard_models_if_empty, ModelRegistryError
)


def test_seed_standard_models():
    seed_standard_models_if_empty()
    models = list_models_3d()
    assert len(models) >= 2
    model_ids = {m["model_id"] for m in models}
    assert "bodyparts3d_v4_ref_torso" in model_ids
    assert "synthetic_torso_v1" in model_ids

    bp3d = get_model_3d("bodyparts3d_v4_ref_torso")
    assert bp3d is not None
    assert bp3d["units"] == "mm"
    assert bp3d["coordinate_frame"] == "mesh_local_xyz"
    assert bp3d["reference_pose"] == "standing_anatomical"
    assert bp3d["handedness"] == "right_handed"
    assert "C7_spinous_process" in bp3d["landmarks"]


def test_register_model_success():
    res = register_model_3d(
        model_id="test_skull_v1",
        name="Test Skull Cranial Reference",
        mesh_id="skull_mesh_01",
        sha256="a" * 64,
        units="mm",
        coordinate_frame="mesh_local_xyz",
        reference_pose="frankfort_horizontal",
        handedness="right_handed",
        landmarks={"nasion": [0.0, 75.0, 40.0]},
        skin_mesh_id="skin_head_surface",
        license="CC-BY-4.0",
        rights_status="ALLOWED"
    )
    assert res["model_id"] == "test_skull_v1"
    assert res["landmarks"]["nasion"] == [0.0, 75.0, 40.0]


def test_register_model_invalid_units():
    with pytest.raises(ModelRegistryError, match="calibrated units"):
        register_model_3d(
            model_id="invalid_units_model",
            name="Invalid Units",
            mesh_id="m1",
            sha256="b" * 64,
            units="inches_uncalibrated",
            skin_mesh_id="skin_1",
            license="MIT"
        )


def test_register_model_invalid_sha():
    with pytest.raises(ModelRegistryError, match="64-character"):
        register_model_3d(
            model_id="invalid_sha_model",
            name="Invalid SHA",
            mesh_id="m1",
            sha256="short_sha",
            units="mm",
            skin_mesh_id="skin_1",
            license="MIT"
        )


def test_register_model_missing_skin_mesh():
    with pytest.raises(ModelRegistryError, match="Designated exterior skin mesh"):
        register_model_3d(
            model_id="no_skin_model",
            name="No Skin",
            mesh_id="m1",
            sha256="c" * 64,
            units="mm",
            skin_mesh_id="",
            license="MIT"
        )
