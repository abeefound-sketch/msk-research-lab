"""Unit tests for Scholarly Tri-Ledger & Fail-Closed Promotion Gates (G7 / R3-02, R3-03)."""

import hashlib
import uuid
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
    get_claim,
    record_evidence,
    get_evidence,
    link_claim_evidence,
    review_evidence,
    record_contradiction,
    promote_claim,
    revise_claim,
    delete_claim_strictly_forbidden,
    PromotionGateError,
    DeletionForbiddenError,
)


@pytest.fixture(autouse=True)
def setup_ledger_db():
    run_migrations()


def create_mock_source_and_locator(source_id: str, locator_id: str):
    cfg = get_config()
    content = f"Educational Text for {source_id}".encode("utf-8")
    sha = hashlib.sha256(content).hexdigest()

    orig_dir = cfg.data_dir / "originals" / sha
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_file = orig_dir / "content"
    orig_file.write_bytes(content)

    register_source(
        source_id=source_id,
        kind="TEXTBOOK",
        canonical_uri=str(orig_file),
        title=f"Source Title {source_id}",
        sha256=sha,
    )
    register_source_location(
        locator_id=locator_id,
        source_id=source_id,
        locator_type="PDF_PAGE",
        locator_details={"page": 10},
    )
    return source_id, locator_id, sha


def test_claim_lifecycle_and_fail_closed_promotion():
    uid = uuid.uuid4().hex[:8]
    src_id, loc_id, _ = create_mock_source_and_locator(f"src:text:{uid}", f"loc:page:{uid}")

    claim_id = f"claim:gb21:trapezius:{uid}"
    claim = create_claim(
        claim_id=claim_id,
        statement="GB21 is located on the highest point of the trapezius muscle ridge.",
        knowledge_namespace="TRADITIONAL_ACUPUNCTURE",
        claim_kind="SOURCE_DESCRIPTION",
    )
    assert claim["status"] == "DRAFT"
    assert claim["review_state"] == "UNREVIEWED"

    # Gate Invariant 1: Fail if automated/AI bot attempts self-promotion
    with pytest.raises(PromotionGateError, match="Reviewer bypass denied"):
        promote_claim(
            claim_id=claim_id,
            target_status="SOURCE_SUPPORTED",
            reviewer_id="ai_agent_autonomous",
            rationale="Auto-promoted by script",
        )

    # Gate Invariant 2: Fail if no supporting evidence is linked
    with pytest.raises(PromotionGateError, match="INSUFFICIENT_VERIFIED_EVIDENCE"):
        promote_claim(
            claim_id=claim_id,
            target_status="SOURCE_SUPPORTED",
            reviewer_id="human_curator_01",
            rationale="Inspected and verified",
        )

    # Record evidence
    ev_id = f"ev:gb21:quote:{uid}"
    ev = record_evidence(
        evidence_id=ev_id,
        source_id=src_id,
        locator_id=loc_id,
        source_kind="TEXTBOOK",
        excerpt_or_observation="At the midpoint of the line connecting C7 and the acromion.",
    )
    link_claim_evidence(
        claim_id=claim_id,
        evidence_id=ev_id,
        relation="SUPPORTS",
        reviewer_rationale="Exact passage matches anatomical description.",
    )

    # Gate Invariant 3: Fail if evidence is still UNREVIEWED (raw OCR or uninspected)
    with pytest.raises(PromotionGateError, match="INSUFFICIENT_VERIFIED_EVIDENCE.*unreviewed state"):
        promote_claim(
            claim_id=claim_id,
            target_status="SOURCE_SUPPORTED",
            reviewer_id="human_curator_01",
            rationale="Inspected and verified",
        )

    # Human reviews evidence
    review_evidence(
        evidence_id=ev_id,
        target_state="CONTENT_REVIEWED",
        reviewer_id="human_curator_01",
        justification="Verified against high-resolution scan of page 10.",
    )

    # Positive Promotion: Human + reviewed evidence + resolved locator
    promoted = promote_claim(
        claim_id=claim_id,
        target_status="SOURCE_SUPPORTED",
        reviewer_id="human_curator_01",
        rationale="Verified against textbook page 10 source passage.",
    )
    assert promoted["status"] == "SOURCE_SUPPORTED"
    assert promoted["review_state"] == "CONTENT_REVIEWED"
    assert promoted["reviewer_id"] == "human_curator_01"


def test_promotion_fails_if_counter_evidence_ignored():
    uid = uuid.uuid4().hex[:8]
    src_id, loc_id, _ = create_mock_source_and_locator(f"src:text:ce_{uid}", f"loc:page:ce_{uid}")

    claim_id = f"claim:gb21:nerve_effect:{uid}"
    claim = create_claim(
        claim_id=claim_id,
        statement="Stimulating GB21 directly activates the accessory nerve for shoulder stiffness.",
        knowledge_namespace="MANUAL_THERAPY",
        claim_kind="INTERVENTION_EFFECT",
    )
    ev_sup_id = f"ev:sup:{uid}"
    record_evidence(
        evidence_id=ev_sup_id,
        source_id=src_id,
        locator_id=loc_id,
        source_kind="TEXTBOOK",
        excerpt_or_observation="Clinical study asserts nerve response.",
    )
    review_evidence(
        evidence_id=ev_sup_id,
        target_state="CONTENT_REVIEWED",
        reviewer_id="human_curator_01",
        justification="Verified text",
    )
    link_claim_evidence(claim_id=claim_id, evidence_id=ev_sup_id, relation="SUPPORTS")

    # Add counter-evidence and register contradiction
    ev_counter_id = f"ev:counter:{uid}"
    record_evidence(
        evidence_id=ev_counter_id,
        source_id=src_id,
        locator_id=loc_id,
        source_kind="TEXTBOOK",
        excerpt_or_observation="Subsequent MRI study found no focal accessory nerve activation.",
    )
    link_claim_evidence(claim_id=claim_id, evidence_id=ev_counter_id, relation="CONTRADICTS")
    record_contradiction(
        contradiction_id=f"cd:nerve:{uid}",
        claim_a_id=claim_id,
        counter_evidence_id=ev_counter_id,
        conflict_kind="CLINICAL_EVIDENCE_CONFLICT",
        rationale="Conflicting imaging findings regarding nerve stimulation.",
    )

    # Promotion without disclosing contradiction must FAIL
    with pytest.raises(PromotionGateError, match="COUNTER_EVIDENCE_DISCLOSURE_REQUIRED"):
        promote_claim(
            claim_id=claim_id,
            target_status="SOURCE_SUPPORTED",
            reviewer_id="human_curator_01",
            rationale="Short note",
            clinical_evidence_assessment="Sample clinical appraisal",
        )

    # Also fails if INTERVENTION_EFFECT lacks clinical_evidence_assessment
    with pytest.raises(PromotionGateError, match="CLINICAL_APPRAISAL_REQUIRED"):
        promote_claim(
            claim_id=claim_id,
            target_status="SOURCE_SUPPORTED",
            reviewer_id="human_curator_01",
            rationale="CONTRADICTION_ACKNOWLEDGED: Reviewed counter-evidence and acknowledged open conflict in literature.",
            clinical_evidence_assessment=None,
        )


def test_claim_revision_and_deletion_guard():
    uid = uuid.uuid4().hex[:8]
    prior_id = f"claim:v1:broad:{uid}"
    next_id = f"claim:v2:narrow:{uid}"

    create_claim(
        claim_id=prior_id,
        statement="Acupoint GB21 cures all upper trapezius tension.",
        knowledge_namespace="TRADITIONAL_ACUPUNCTURE",
        claim_kind="TRADITIONAL_THEORY",
    )

    # Revision creates successor and marks prior REVISED
    revised = revise_claim(
        prior_claim_id=prior_id,
        next_claim_id=next_id,
        new_statement="Traditional sources describe GB21 as indicated for regional shoulder and neck stiffness.",
        reason="Over-broad assertion narrowed to specific source indications.",
    )
    assert revised["claim_id"] == next_id
    assert revised["supersedes_claim_id"] == prior_id

    prior = get_claim(prior_id)
    assert prior["status"] == "REVISED"

    # Strictly forbid hard deletion
    with pytest.raises(DeletionForbiddenError, match="Hard deletion.*is forbidden"):
        delete_claim_strictly_forbidden(prior_id)

