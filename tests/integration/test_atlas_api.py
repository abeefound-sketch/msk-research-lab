"""Integration tests for Atlas & Surface Registration API (ATLAS-01..04 / R4)."""

import pytest
from fastapi.testclient import TestClient
from msk_research_lab.api.app import app
from msk_research_lab.atlas.registry import seed_standard_models_if_empty

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_seeded():
    seed_standard_models_if_empty()


def test_api_list_models():
    res = client.get("/api/v1/atlas/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert len(data["models"]) >= 2
    model_ids = [m["model_id"] for m in data["models"]]
    assert "bodyparts3d_v4_ref_torso" in model_ids


def test_api_get_model_details():
    res = client.get("/api/v1/atlas/models/bodyparts3d_v4_ref_torso")
    assert res.status_code == 200
    data = res.json()
    assert data["model_id"] == "bodyparts3d_v4_ref_torso"
    assert data["units"] == "mm"
    assert data["coordinate_frame"] == "mesh_local_xyz"
    assert "C7_spinous_process" in data["landmarks"]

    # 404 for unknown model
    res_404 = client.get("/api/v1/atlas/models/nonexistent_model_xyz")
    assert res_404.status_code == 404


def test_api_inspect_point_gb21():
    res = client.get("/api/v1/atlas/points/GB21")
    assert res.status_code == 200
    data = res.json()
    assert data["point_code"] == "GB21"
    assert "concept" in data
    assert "placements_3d" in data
    assert "regional_anatomy" in data
    assert "disclaimer" in data

    # Verify regional anatomy layers
    layers = [l["layer"] for l in data["regional_anatomy"]]
    assert "integumentary" in layers
    assert "muscular_superficial" in layers
    assert "muscular_deep" in layers
    assert "skeletal" in layers
    assert "nervous" in layers


def test_api_surface_snap():
    payload = {
        "x": -97.5,
        "y": 475.0,
        "z": -45.0,
        "tolerance_mm": 5.0,
        "triangles": [
            [[-97.5, 475.0, -45.0], [-105.0, 472.0, -40.0], [-90.0, 470.0, -50.0]]
        ]
    }
    res = client.post("/api/v1/atlas/surface/snap", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASS"
    assert data["distance_mm"] <= 0.01
    assert len(data["barycentric"]) == 3


def test_api_compare_unregistered_blocked():
    payload = {
        "point_code": "GB21",
        "placement_a": {
            "source_id": "src_1",
            "model_id": "mesh_a",
            "frame_registered": False,
            "x": 10.0, "y": 20.0, "z": 30.0
        },
        "placement_b": {
            "source_id": "src_2",
            "model_id": "mesh_b",
            "frame_registered": False,
            "x": 12.0, "y": 20.0, "z": 30.0
        }
    }
    res = client.post("/api/v1/atlas/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "NOT_COMPARABLE"
    assert data["geometric_comparability_state"] == "UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL"
    assert data["measured_distance_mm"] is None


def test_api_get_meridian_path():
    res = client.get("/api/v1/atlas/meridians/GB")
    assert res.status_code == 200
    data = res.json()
    assert data["meridian_code"] == "GB"
    assert "baked_segments" in data
    assert len(data["baked_segments"]) > 0


def test_api_bake_meridian_path():
    payload = {
        "path_id": "api_test_meridian_bake_01",
        "meridian_code": "LU",
        "control_points": [
            [-97.5, 475.0, -45.0],
            [-105.0, 472.0, -40.0]
        ],
        "triangles": [
            [[-97.5, 475.0, -45.0], [-105.0, 472.0, -40.0], [-90.0, 470.0, -50.0]]
        ],
        "penetration_tolerance_mm": 20.0
    }
    res = client.post("/api/v1/atlas/meridians/bake", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["meridian_code"] == "LU"
    assert data["has_penetration_gap"] is False
    assert data["segment_count"] == 1
