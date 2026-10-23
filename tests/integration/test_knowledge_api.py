"""Integration tests for Published Knowledge API & Therapy Interoperability (G10 / R3-08)."""

import pytest
from fastapi.testclient import TestClient

from msk_research_lab.api.app import app
from msk_research_lab.core.config import get_config
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.ontology.lookup import load_ontology_seed
from msk_research_lab.publication.publisher import (
    stage_snapshot_build,
    promote_release,
    rollback_release,
)
from tests.unit.test_snapshot_publisher import seed_valid_published_claim

client = TestClient(app)
VALID_TOKEN = "valid-test-token"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_TOKEN}"}


@pytest.fixture(autouse=True)
def setup_api_env():
    run_migrations()
    cfg = get_config()
    active_ptr = cfg.data_dir / "snapshots" / ".active" / "current.json"
    if active_ptr.exists():
        active_ptr.unlink()
    yield
    if active_ptr.exists():
        active_ptr.unlink()




def test_auth_safeguards():
    # 1. No bearer token -> 401 Unauthorized
    res_no_auth = client.get("/api/v1/snapshots/current")
    assert res_no_auth.status_code == 401

    # 2. Invalid token -> 403 Forbidden
    res_bad_auth = client.get("/api/v1/snapshots/current", headers={"Authorization": "Bearer bad-token-xyz"})
    assert res_bad_auth.status_code == 403

    # 3. Valid token -> 200 OK
    res_ok = client.get("/api/v1/snapshots/current", headers=AUTH_HEADER)
    assert res_ok.status_code == 200


def test_published_endpoints_before_and_after_snapshot():
    import uuid
    uid = uuid.uuid4().hex[:8]
    build_id = f"build_api_{uid}"
    rel_id = f"rel_api_{uid}"
    claim_id = f"claim:pub:gb21_{uid}"

    # Before snapshot publication:
    # GET /api/v1/knowledge/points/GB21 must return 404 UNREVIEWED_NOT_PUBLISHED
    res_pre = client.get("/api/v1/knowledge/points/GB21", headers=AUTH_HEADER)
    assert res_pre.status_code == 404
    assert res_pre.json()["detail"]["code"] == "UNREVIEWED_NOT_PUBLISHED"

    # Seed data and publish snapshot
    load_ontology_seed()
    seed_valid_published_claim(claim_id)

    stage_snapshot_build(build_id=build_id, operator_id="lead_eng")
    promote_release(build_id=build_id, release_id=rel_id, operator_id="lead_eng")

    # 1. Active snapshot status
    res_snap = client.get("/api/v1/snapshots/current", headers=AUTH_HEADER)
    assert res_snap.status_code == 200
    snap_data = res_snap.json()
    assert snap_data["active"] is True
    assert snap_data["snapshot_id"] == rel_id

    # 2. Point knowledge endpoint now resolves from active snapshot!
    res_pt = client.get("/api/v1/knowledge/points/GB21", headers=AUTH_HEADER)
    assert res_pt.status_code == 200
    pt_data = res_pt.json()
    assert pt_data["code"] == "GB21"
    assert pt_data["concept_id"] == "tcm:acupoint:GB21"
    assert pt_data["snapshot_id"] == rel_id
    assert "disclaimer" in pt_data

    # 3. Published claim endpoint
    res_cl = client.get(f"/api/v1/claims/{claim_id}", headers=AUTH_HEADER)
    assert res_cl.status_code == 200
    cl_data = res_cl.json()
    assert cl_data["claim_id"] == claim_id
    assert cl_data["status"] == "SOURCE_SUPPORTED"
    assert cl_data["snapshot_id"] == rel_id
    assert len(cl_data["source_evidence"]) >= 1

    # 4. Unreviewed claim / non-existent claim returns 404
    res_unrev = client.get("/api/v1/claims/claim:non_existent", headers=AUTH_HEADER)
    assert res_unrev.status_code == 404
    assert res_unrev.json()["detail"]["code"] == "UNREVIEWED_NOT_PUBLISHED"

    # 5. Multilingual ontology lookup endpoint
    res_ont = client.get("/api/v1/ontology/lookup?term=Jianjing", headers=AUTH_HEADER)
    assert res_ont.status_code == 200
    ont_data = res_ont.json()
    assert ont_data["count"] >= 1
    assert ont_data["results"][0]["concept_id"] == "tcm:acupoint:GB21"

