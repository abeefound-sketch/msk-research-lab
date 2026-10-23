"""Integration tests for Repository Lab API endpoints."""

from fastapi.testclient import TestClient
from msk_research_lab.api.app import app

client = TestClient(app)


def test_list_repositories():
    response = client.get("/api/v1/repos")
    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data
    assert len(data["repositories"]) >= 1


def test_register_and_inspect_repository():
    import uuid
    uid = uuid.uuid4().hex[:6]
    # 1. Register a new repository
    reg_res = client.post(
        "/api/v1/repos/register",
        json={
            "url": f"https://github.com/test-org/test-anatomy-{uid}.git",
            "name": f"Test Anatomy Project {uid}",
            "category": "ANATOMY_3D"
        }
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    repo_id = reg_data["repo_id"]
    assert repo_id == f"test-org--test-anatomy-{uid}"

    # 2. Inspect the repository statically
    insp_res = client.post(f"/api/v1/repos/{repo_id}/inspect")
    assert insp_res.status_code == 200
    insp_data = insp_res.json()
    assert insp_data["status"] == "INSPECTED"

    # 3. Approve run profile
    appr_res = client.post(
        f"/api/v1/repos/{repo_id}/approve",
        json={"profile_id": "profile-static-1", "commit_sha": "abc1234567890abcdef1234567890abcdef1234"}
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "APPROVED"
    assert "token" in appr_res.json()

    # 4. Attempt launch -> Must be BLOCKED with 503 under Option B (no bare-metal execution)
    launch_res = client.post(f"/api/v1/repos/{repo_id}/launch")
    assert launch_res.status_code == 503
    assert launch_res.json()["detail"]["code"] == "SANDBOX_UNAVAILABLE"


def test_surface_registration_benchmark_endpoint():
    res = client.get("/api/v1/benchmarks/surface-registration")
    assert res.status_code == 200
    data = res.json()
    assert data["suite"] == "surface-registration-v1"
    assert data["total_cases"] == 10
    assert data["passed"] == 10
    assert data["overall_status"] == "PASS"
