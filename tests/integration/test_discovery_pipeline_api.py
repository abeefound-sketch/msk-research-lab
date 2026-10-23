"""Integration tests for R1D Discovery & Research Pipeline APIs and Dashboard."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from msk_research_lab.api.app import app
from msk_research_lab.core.config import get_config
from msk_research_lab.core.migrations import run_migrations


@pytest.fixture(scope="module")
def client():
    run_migrations()
    with TestClient(app) as c:
        yield c


def test_api_discovery_import_markdown(client):
    cfg = get_config()
    ref_file = cfg.root_dir / "research" / "references" / "awesome_msk_biomedical_repos.md"
    assert ref_file.exists()

    resp = client.post("/api/v1/discovery/import-markdown", json={"file_path": str(ref_file)})
    assert resp.status_code == 200
    data = resp.json()
    assert "document_id" in data
    assert data["candidate_count"] >= 3
    assert data["occurrence_count"] >= 3


def test_api_discovery_import_markdown_security_rejection(client):
    resp = client.post("/api/v1/discovery/import-markdown", json={"file_path": "/etc/passwd"})
    assert resp.status_code == 400
    assert "outside allowlisted directory" in resp.json()["detail"]


def test_api_get_discovery_candidates(client):
    resp = client.get("/api/v1/discovery/candidates")
    assert resp.status_code == 200
    cands = resp.json()
    assert isinstance(cands, list)
    assert len(cands) >= 1
    # Check status of discovered candidate
    first = cands[0]
    assert "canonical_url" in first
    assert "status" in first


def test_api_get_discovery_candidate_detail(client):
    cands_resp = client.get("/api/v1/discovery/candidates")
    first_id = cands_resp.json()[0]["id"]

    resp = client.get(f"/api/v1/discovery/candidates/{first_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidate"]["id"] == first_id
    assert "occurrences" in data
    assert "decisions" in data


def test_api_github_search_and_save(client):
    # Live or mock search
    search_resp = client.post("/api/v1/discovery/github-search", json={
        "keywords": "biomechanics musculoskeletal",
        "per_page": 2
    })
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert "status" in data
    assert "items" in data

    # Save a candidate item
    item_payload = {
        "owner": "mockbiomed",
        "repo": "msk-tools",
        "canonical_url": "https://github.com/mockbiomed/msk-tools",
        "description": "Musculoskeletal biomechanical model utilities",
        "primary_language": "Python",
        "license_spdx": "Apache-2.0",
        "stars_count": 88
    }
    save_resp = client.post("/api/v1/discovery/candidates/save", json={
        "item": item_payload,
        "priority": "HIGH"
    })
    assert save_resp.status_code == 200
    cand_id = save_resp.json()["candidate_id"]
    assert cand_id == "cand_mockbiomed_msk-tools"


def test_api_research_queue(client):
    resp = client.post("/api/v1/research/queue", json={
        "candidate_id": "cand_mockbiomed_msk-tools",
        "priority": "URGENT",
        "tags": ["biomechanics", "kinematics"],
        "research_questions": ["Does it compute joint angles?"]
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESEARCH_QUEUED"
    assert resp.json()["priority"] == "URGENT"


def test_api_research_compare(client):
    resp = client.post("/api/v1/research/compare", json={
        "candidate_ids": ["cand_openanatomy_open-anatomy-browser", "cand_mockbiomed_msk-tools"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["compared_candidates_count"] == 2
    assert "comparison_matrix" in data


def test_api_research_decisions(client):
    resp = client.post("/api/v1/research/decisions", json={
        "candidate_id": "cand_mockbiomed_msk-tools",
        "decision": "ADAPT",
        "justification": "Useful joint angle coordinate logic to integrate into MSK kinematic engine.",
        "reviewed_by": "LEAD_ARCHITECT"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "ADAPT"
    assert data["reviewed_by"] == "LEAD_ARCHITECT"


def test_api_research_report_generation(client):
    resp = client.post("/api/v1/research/reports", json={
        "candidate_id": "cand_mockbiomed_msk-tools",
        "reviewer": "LEAD_ARCHITECT"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    assert "manifest_sha256" in data
    assert "tri_ledger_evidence_id" in data

    # Retrieve report via GET
    rep_get = client.get(f"/api/v1/research/reports/{data['report_id']}")
    assert rep_get.status_code == 200
    rep_data = rep_get.json()
    assert rep_data["candidate_id"] == "cand_mockbiomed_msk-tools"
    assert "Scholarly Research Report" in rep_data["markdown_content"]


def test_api_rea_status(client):
    resp = client.get("/api/v1/research/rea/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_available" in data
    assert "status" in data


def test_dashboard_renders_r1d_and_rebaselined_gates(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    html = resp.text
    assert "Discovery &amp; Research Pipeline Candidates (R1D" in html or "Discovery & Research Pipeline Candidates (R1D" in html
    assert ("BLOCKED (WSL)" in html or "BLOCKED (APPROVAL REQ)" in html)
    assert "R1D: Discovery" in html
    assert "PASS" in html
