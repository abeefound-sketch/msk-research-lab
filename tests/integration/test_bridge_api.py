"""Integration tests for Therapy Delivery Bridge & Security Invariants (BRIDGE-01..03 / R6)."""

import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from msk_research_lab.api.app import app
from msk_research_lab.core.config import get_config
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.ontology.lookup import load_ontology_seed
from msk_research_lab.publication.publisher import stage_snapshot_build, promote_release
from tests.unit.test_snapshot_publisher import seed_valid_published_claim
from msk_research_lab.bridge.mock_consumer import TherapyResearchClient, AuthenticationError

client = TestClient(app)
VALID_TOKEN = "valid-test-token"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_TOKEN}"}


@pytest.fixture
def active_snapshot_ready():
    """Ensure an active validated snapshot is published for the bridge tests and cleaned up after."""
    run_migrations()
    load_ontology_seed()

    cfg = get_config()
    active_ptr = cfg.data_dir / "snapshots" / ".active" / "current.json"
    if active_ptr.exists():
        active_ptr.unlink()

    uid = uuid.uuid4().hex[:8]
    build_id = f"build_bridge_{uid}"
    rel_id = f"rel_bridge_{uid}"
    claim_id = f"claim:pub:bridge_{uid}"

    seed_valid_published_claim(claim_id)
    stage_snapshot_build(build_id=build_id, operator_id="lead_eng")
    rel = promote_release(build_id=build_id, release_id=rel_id, operator_id="lead_eng")

    yield rel

    if active_ptr.exists():
        active_ptr.unlink()


def test_bridge_package_export_and_verify(active_snapshot_ready):
    payload = {"package_id": "pkg_bridge_int_test_01"}

    # Unauthorized request rejected (401)
    res_unauth = client.post("/api/v1/bridge/packages/export", json=payload)
    assert res_unauth.status_code == 401

    # Authorized export
    res_auth = client.post("/api/v1/bridge/packages/export", headers=AUTH_HEADER, json=payload)
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "EXPORTED"
    assert data["package_id"] == "pkg_bridge_int_test_01"
    manifest_path = data["manifest_path"]

    # Verify package via API
    res_ver = client.post(
        "/api/v1/bridge/packages/verify",
        json={"package_path": str(Path(manifest_path).parent)}
    )
    assert res_ver.status_code == 200
    assert res_ver.json()["status"] == "VALID"


def test_bridge_security_invariants_raw_and_process_rejection(active_snapshot_ready):
    """BRIDGE-03: Raw binary document dumps, process executions, and private drafts are not exposed."""
    # Process execution is disabled/blocked by default
    res_run = client.post("/api/v1/repos/open-anatomy-atlas/run", json={"profile_name": "default"})
    assert res_run.status_code in {400, 403, 404}

    # Knowledge point endpoint delivers reviewed data without leaking patient records or raw books
    res_pt = client.get("/api/v1/knowledge/points/GB21", headers=AUTH_HEADER)
    assert res_pt.status_code == 200
    pt_data = res_pt.json()
    assert "patient" not in str(pt_data).lower()
    assert pt_data["code"] == "GB21"
    assert "disclaimer" in pt_data
