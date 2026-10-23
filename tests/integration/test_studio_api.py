"""Integration tests for Studio & 2D Diện Chẩn API (ATLAS-05..06 / R5)."""

import pytest
from fastapi.testclient import TestClient
from msk_research_lab.api.app import app
from msk_research_lab.studio.dien_chan import initialize_dien_chan_project

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_studio_initialized():
    initialize_dien_chan_project("proj_dien_chan_api_fixture")


def test_api_list_and_create_studio_projects():
    # List
    res_list = client.get("/api/v1/studio/projects")
    assert res_list.status_code == 200
    data = res_list.json()
    assert "projects" in data
    assert len(data["projects"]) >= 1

    # Create new
    payload = {
        "project_id": "proj_api_create_01",
        "title": "API Created Project",
        "namespace": "THAI_SEN",
        "description": "Created via REST API",
        "license": "CC-BY-SA 4.0"
    }
    res_create = client.post("/api/v1/studio/projects", json=payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["project_id"] == "proj_api_create_01"
    assert created["namespace"] == "THAI_SEN"


def test_api_add_move_delete_and_undo_point():
    # 1. Add point
    pt_payload = {
        "point_id": "pt_api_point_01",
        "code": "API_PT_01",
        "canonical_label": "API Test Point",
        "dimensionality": "2D_IMAGE_PIXEL",
        "point_kind": "FIXED_EDUCATIONAL",
        "image_sha256": "f" * 64,
        "image_view": "FRONT",
        "pixel_xy": [120.0, 180.0],
        "notes": "Test point notes"
    }
    res_add = client.post("/api/v1/studio/projects/proj_dien_chan_api_fixture/points", json=pt_payload)
    assert res_add.status_code == 200
    pt = res_add.json()
    assert pt["code"] == "API_PT_01"

    # 2. Move point
    move_payload = {
        "pixel_xy": [130.0, 190.0]
    }
    res_move = client.put(
        "/api/v1/studio/projects/proj_dien_chan_api_fixture/points/pt_api_point_01",
        json=move_payload
    )
    assert res_move.status_code == 200
    moved = res_move.json()
    assert moved["x_px"] == 130.0

    # 3. Undo move
    res_undo = client.post("/api/v1/studio/projects/proj_dien_chan_api_fixture/undo")
    assert res_undo.status_code == 200
    undo_data = res_undo.json()
    assert undo_data["undone_action"] == "MOVE_POINT"

    # 4. Delete point
    res_del = client.delete("/api/v1/studio/projects/proj_dien_chan_api_fixture/points/pt_api_point_01")
    assert res_del.status_code == 200
    assert res_del.json()["is_deleted"] == 1


def test_api_export_and_import_project():
    # Export
    res_exp = client.post("/api/v1/studio/projects/proj_dien_chan_api_fixture/export")
    assert res_exp.status_code == 200
    bundle = res_exp.json()
    assert bundle["schema_version"] == "3.0.0"
    assert "points_sha256" in bundle

    # Import with new ID
    bundle["project"]["project_id"] = "proj_api_imported_01"
    for p in bundle["points"]:
        p["project_id"] = "proj_api_imported_01"
        p["point_id"] = f"{p['point_id']}_copy"

    res_imp = client.post("/api/v1/studio/projects/import", json={"payload": bundle, "overwrite": True})
    assert res_imp.status_code == 200
    imp_data = res_imp.json()
    assert imp_data["status"] == "IMPORTED"
    assert imp_data["imported_point_count"] >= 1


def test_api_get_dien_chan_baseline():
    res = client.get("/api/v1/studio/dien-chan/baseline")
    assert res.status_code == 200
    data = res.json()
    assert "baseline_points" in data
    codes = [p["code"] for p in data["baseline_points"]]
    assert "DC_19" in codes
    assert "DC_0" in codes
