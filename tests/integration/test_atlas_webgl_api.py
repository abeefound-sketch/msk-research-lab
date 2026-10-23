"""Integration tests for Atlas WebGL 3D Scene API and Static Assets (ATLAS-01..06 / R4)."""

import pytest
from fastapi.testclient import TestClient
from msk_research_lab.api.app import app

client = TestClient(app)


def test_static_vendor_threejs_delivered():
    """Verify Three.js and OrbitControls vendor scripts are served statically."""
    res_three = client.get("/static/vendor/three.min.js")
    assert res_three.status_code == 200
    assert "javascript" in res_three.headers.get("content-type", "").lower()
    assert len(res_three.content) > 100000

    res_orbit = client.get("/static/vendor/OrbitControls.js")
    assert res_orbit.status_code == 200
    assert "javascript" in res_orbit.headers.get("content-type", "").lower()
    assert len(res_orbit.content) > 10000


def test_api_get_atlas_scene_geometry():
    """Verify GET /api/v1/atlas/scene/{model_id} returns verified calibrated 3D meshes and points."""
    res = client.get("/api/v1/atlas/scene/bodyparts3d_v4_ref_torso")
    assert res.status_code == 200
    data = res.json()

    assert data["model_id"] == "bodyparts3d_v4_ref_torso"
    assert data["units"] == "mm"
    assert data["coordinate_frame"] == "mesh_local_xyz"
    assert "landmarks" in data
    assert "C7_spinous_process" in data["landmarks"]

    # Verify 5 Anatomical Layers
    layers = data["layers"]
    assert "skin" in layers
    assert "skeletal" in layers
    assert "superficial_muscle" in layers
    assert "deep_muscle" in layers
    assert "nerves" in layers

    assert len(layers["skin"]["vertices"]) > 100
    assert len(layers["skin"]["indices"]) > 100
    assert layers["skin"]["opacity"] == pytest.approx(0.45, rel=1e-2)

    # Verify Anchored Points
    points = data["points"]
    assert len(points) >= 5
    point_codes = [p["code"] for p in points]
    assert "GB21" in point_codes
    assert "GV14" in point_codes
    assert "SI14" in point_codes
    assert "SI15" in point_codes
    assert "BL11" in point_codes

    # Verify Meridian Trajectories
    meridians = data["meridians"]
    m_codes = [m["code"] for m in meridians]
    assert "GB" in m_codes
    assert "SI" in m_codes

    # Verify 6 Standard Camera Presets
    presets = data["camera_presets"]
    assert "FRONT" in presets
    assert "BACK" in presets
    assert "LEFT" in presets
    assert "RIGHT" in presets
    assert "OBLIQUE_TOP" in presets
    assert "OBLIQUE_BOTTOM" in presets
    assert "RESET" in presets


def test_dashboard_contains_webgl_threejs_and_workbench():
    """Verify Dashboard HTML includes Three.js scripts, 3D WebGL container, and layer toggles."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert "/static/vendor/three.min.js" in html
    assert "/static/vendor/OrbitControls.js" in html
    assert "webglContainer" in html
    assert "regionFilter" in html
    assert "pointSelect" in html
    assert "bodyparts3d_v4_ref_torso" in html
    assert "SHOULDER_RIDGE" in html
    assert "GB21" in html
    assert "Epistemic Disclaimer" in html
