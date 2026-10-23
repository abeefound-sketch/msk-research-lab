"""Unit tests for Knowledge Snapshot Publisher & Disaster Rollback (G10 / R3-07)."""

import hashlib
import json
import pytest
from pathlib import Path

from msk_research_lab.core.config import get_config
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.provenance.registry import (
    register_source,
    register_source_location,
)
from msk_research_lab.ledgers.claims import (
    create_claim,
    record_evidence,
    link_claim_evidence,
    review_evidence,
    promote_claim,
)
from msk_research_lab.ontology.lookup import load_ontology_seed
from msk_research_lab.publication.publisher import (
    stage_snapshot_build,
    promote_release,
    rollback_release,
    get_active_release,
    QAGateError,
    PublicationError,
)


@pytest.fixture(autouse=True)
def setup_publisher_db():
    run_migrations()
    yield
    cfg = get_config()
    active_ptr = cfg.data_dir / "snapshots" / ".active" / "current.json"
    if active_ptr.exists():
        active_ptr.unlink()



def seed_valid_published_claim(claim_id: str = "claim:pub:001"):
    cfg = get_config()
    content = b"Published Evidence Excerpt for Acupoint GB21"
    sha = hashlib.sha256(content).hexdigest()

    orig_dir = cfg.data_dir / "originals" / sha
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_file = orig_dir / "content"
    orig_file.write_bytes(content)

    src_id = f"src:pub:{claim_id}"
    loc_id = f"loc:pub:{claim_id}"

    register_source(
        source_id=src_id,
        kind="TEXTBOOK",
        canonical_uri=str(orig_file),
        title="Valid Source For Publication",
        sha256=sha,
    )
    register_source_location(
        locator_id=loc_id,
        source_id=src_id,
        locator_type="PDF_PAGE",
        locator_details={"page": 15},
    )

    create_claim(
        claim_id=claim_id,
        statement="Educational source description for GB21 landmark.",
        knowledge_namespace="TRADITIONAL_ACUPUNCTURE",
        claim_kind="SOURCE_DESCRIPTION",
    )
    record_evidence(
        evidence_id=f"ev:pub:{claim_id}",
        source_id=src_id,
        locator_id=loc_id,
        source_kind="TEXTBOOK",
        excerpt_or_observation="Exact landmark citation text.",
    )
    review_evidence(
        evidence_id=f"ev:pub:{claim_id}",
        target_state="CONTENT_REVIEWED",
        reviewer_id="lead_reviewer_01",
        justification="Verified text",
    )
    link_claim_evidence(
        claim_id=claim_id,
        evidence_id=f"ev:pub:{claim_id}",
        relation="SUPPORTS",
    )
    promote_claim(
        claim_id=claim_id,
        target_status="SOURCE_SUPPORTED",
        reviewer_id="lead_reviewer_01",
        rationale="Verified and approved for publication snapshot.",
    )


def test_stage_build_and_promote_release():
    import uuid
    uid = uuid.uuid4().hex[:8]
    build_id = f"build_r3_{uid}"
    rel_id = f"rel_test_{uid}"

    load_ontology_seed()
    seed_valid_published_claim(f"claim:pub:gb21:{uid}")

    # 1. Stage snapshot build
    build = stage_snapshot_build(build_id=build_id, operator_id="operator_01")
    assert build["build_id"] == build_id
    assert build["qa"]["qa_passed"] is True
    assert build["manifest"]["published_claims_count"] >= 1

    # 2. Promote to active release
    rel = promote_release(build_id=build_id, release_id=rel_id, operator_id="operator_01")
    assert rel["release_id"] == rel_id
    assert "manifest_hash" in rel

    # 3. Verify active pointer
    active = get_active_release()
    assert active is not None
    assert active["release_id"] == rel_id
    assert Path(active["db_path"]).exists()


def test_rollback_to_prior_release():
    import uuid
    uid = uuid.uuid4().hex[:8]
    build_v1 = f"build_v1_{uid}"
    rel_v1 = f"rel_v1_{uid}"
    build_v2 = f"build_v2_{uid}"
    rel_v2 = f"rel_v2_{uid}"

    load_ontology_seed()
    seed_valid_published_claim(f"claim:pub:v1:{uid}")

    # Build and promote Release 1
    stage_snapshot_build(build_id=build_v1, operator_id="operator_01")
    promote_release(build_id=build_v1, release_id=rel_v1, operator_id="operator_01")
    assert get_active_release()["release_id"] == rel_v1

    # Build and promote Release 2
    stage_snapshot_build(build_id=build_v2, operator_id="operator_01")
    promote_release(build_id=build_v2, release_id=rel_v2, operator_id="operator_01")
    assert get_active_release()["release_id"] == rel_v2

    # Execute atomic rollback to Release 1
    rolled_back = rollback_release(target_release_id=rel_v1, operator_id="operator_01")
    assert rolled_back["release_id"] == rel_v1
    assert rolled_back["is_rollback"] is True

    # Active pointer must now point to Release 1
    current = get_active_release()
    assert current["release_id"] == rel_v1

