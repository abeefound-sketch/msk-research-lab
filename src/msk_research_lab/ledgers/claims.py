"""Scholarly Tri-Ledger: Claims, Evidence, and Contradictions (G7 / R3-02, R3-03).

Implements auditable claims, evidence attribution, dispute tracking,
fail-closed promotion gates, revision lineage, and human review logs.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from msk_research_lab.core.db import get_db
from msk_research_lab.provenance.registry import (
    get_source,
    get_source_location,
    resolve_source_locator,
    LocatorResolutionError,
)

ALLOWLISTED_NAMESPACES = {
    "SOMATIC_ANATOMY",
    "TRADITIONAL_ACUPUNCTURE",
    "TRADITIONAL_DIEN_CHAN",
    "TRADITIONAL_THAI_SEN",
    "MANUAL_THERAPY",
    "BIOMECHANICS",
    "DEVICE_TECHNOLOGY",
    "SOFTWARE_ENGINEERING",
}

ALLOWLISTED_CLAIM_KINDS = {
    "SOURCE_DESCRIPTION",
    "ANATOMICAL_FACT",
    "TRADITIONAL_THEORY",
    "HYPOTHESIS",
    "GEOMETRIC_ASSERTION",
    "INTERVENTION_EFFECT",
    "TECHNICAL_FINDING",
}

ALLOWLISTED_CLAIM_STATUSES = {
    "DRAFT",
    "PROVISIONAL",
    "SOURCE_SUPPORTED",
    "DISPUTED",
    "REVISED",
    "REJECTED",
}

ALLOWLISTED_REVIEW_STATES = {
    "UNREVIEWED",
    "LOCATOR_VERIFIED",
    "CONTENT_REVIEWED",
    "DOMAIN_REVIEWED",
    "REJECTED",
}

ALLOWLISTED_CONFLICT_KINDS = {
    "TRANSLATION_DIFFERENCE",
    "SOURCE_DISAGREEMENT",
    "MEASUREMENT_DIFFERENCE",
    "METHODOLOGICAL_LIMITATION",
    "CLINICAL_EVIDENCE_CONFLICT",
    "ALIAS_VARIANT",
}


class LedgerError(Exception):
    """Base exception for tri-ledger errors."""
    pass


class PromotionGateError(LedgerError):
    """Raised when a claim fails the fail-closed promotion requirements."""
    pass


class DeletionForbiddenError(LedgerError):
    """Raised when an attempt is made to delete referenced evidence or claims."""
    pass


def create_claim(
    *,
    claim_id: str,
    statement: str,
    knowledge_namespace: str,
    claim_kind: str,
    author_kind: str = "RESEARCHER",
    uncertainty_text: Optional[str] = None,
    supersedes_claim_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new proposition in the Claims Ledger with initial status DRAFT."""
    if knowledge_namespace not in ALLOWLISTED_NAMESPACES:
        raise LedgerError(f"Invalid namespace '{knowledge_namespace}'. Allowed: {sorted(ALLOWLISTED_NAMESPACES)}")
    if claim_kind not in ALLOWLISTED_CLAIM_KINDS:
        raise LedgerError(f"Invalid claim kind '{claim_kind}'. Allowed: {sorted(ALLOWLISTED_CLAIM_KINDS)}")

    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO claims (
                claim_id, statement, knowledge_namespace, claim_kind,
                status, author_kind, review_state, supersedes_claim_id,
                uncertainty_text, created_at, revised_at
            ) VALUES (?, ?, ?, ?, 'DRAFT', ?, 'UNREVIEWED', ?, ?, ?, ?)
            ON CONFLICT(claim_id) DO UPDATE SET
                statement=excluded.statement,
                knowledge_namespace=excluded.knowledge_namespace,
                claim_kind=excluded.claim_kind,
                supersedes_claim_id=excluded.supersedes_claim_id,
                uncertainty_text=excluded.uncertainty_text,
                revised_at=excluded.revised_at;
            """,
            (
                claim_id, statement, knowledge_namespace, claim_kind,
                author_kind, supersedes_claim_id, uncertainty_text, now_iso, now_iso
            )
        )
    return get_claim(claim_id)


def get_claim(claim_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve claim details with linked evidence and open contradictions."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM claims WHERE claim_id = ?;", (claim_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)

        # Linked evidence
        cur_ev = conn.execute(
            """
            SELECT e.*, l.relation, l.reviewer_rationale
            FROM evidence e
            JOIN claim_evidence_links l ON e.evidence_id = l.evidence_id
            WHERE l.claim_id = ?;
            """,
            (claim_id,)
        )
        res["linked_evidence"] = [dict(r) for r in cur_ev.fetchall()]

        # Contradictions
        cur_cd = conn.execute(
            """
            SELECT * FROM contradictions
            WHERE claim_a_id = ? OR claim_b_id = ?;
            """,
            (claim_id, claim_id)
        )
        res["contradictions"] = [dict(r) for r in cur_cd.fetchall()]

        return res


def record_evidence(
    *,
    evidence_id: str,
    source_id: str,
    locator_id: str,
    source_kind: str,
    excerpt_or_observation: str,
    extraction_method: str = "MANUAL",
    original_language: Optional[str] = None,
    edition_id: Optional[str] = None,
    author_kind: str = "RESEARCHER",
    independence_group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a traceable excerpt or measurement into the Evidence Ledger."""
    source = get_source(source_id)
    if not source:
        raise LedgerError(f"Source '{source_id}' does not exist.")

    location = get_source_location(locator_id)
    if not location:
        raise LedgerError(f"Locator '{locator_id}' does not exist.")

    eff_group = independence_group_id or source.get("independence_group_id") or source_id
    prov_seed = f"{source_id}:{locator_id}:{excerpt_or_observation}"
    prov_hash = hashlib.sha256(prov_seed.encode("utf-8")).hexdigest()
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO evidence (
                evidence_id, source_id, locator_id, source_kind,
                excerpt_or_observation, extraction_method, review_state,
                provenance_hash, original_language, edition_id,
                author_kind, independence_group_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'UNREVIEWED', ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                excerpt_or_observation=excluded.excerpt_or_observation,
                provenance_hash=excluded.provenance_hash;
            """,
            (
                evidence_id, source_id, locator_id, source_kind,
                excerpt_or_observation, extraction_method, prov_hash,
                original_language, edition_id, author_kind, eff_group, now_iso
            )
        )
    return get_evidence(evidence_id)


def get_evidence(evidence_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve evidence details by evidence_id."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM evidence WHERE evidence_id = ?;", (evidence_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def link_claim_evidence(
    *,
    claim_id: str,
    evidence_id: str,
    relation: str,
    reviewer_rationale: Optional[str] = None,
) -> None:
    """Link an evidence record to a claim with relation SUPPORTS, CONTRADICTS, or CONTEXT."""
    if relation not in {"SUPPORTS", "CONTRADICTS", "CONTEXT"}:
        raise LedgerError(f"Invalid relation '{relation}'. Allowed: SUPPORTS, CONTRADICTS, CONTEXT")

    claim = get_claim(claim_id)
    if not claim:
        raise LedgerError(f"Claim '{claim_id}' not found.")
    evidence = get_evidence(evidence_id)
    if not evidence:
        raise LedgerError(f"Evidence '{evidence_id}' not found.")

    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO claim_evidence_links (
                claim_id, evidence_id, relation, reviewer_rationale
            ) VALUES (?, ?, ?, ?);
            """,
            (claim_id, evidence_id, relation, reviewer_rationale)
        )


def review_evidence(
    *,
    evidence_id: str,
    target_state: str,
    reviewer_id: str,
    justification: str,
) -> Dict[str, Any]:
    """Human review of evidence record."""
    if target_state not in {"CONTENT_REVIEWED", "DOMAIN_REVIEWED", "REJECTED"}:
        raise LedgerError(f"Invalid review state '{target_state}' for evidence.")
    if not reviewer_id or reviewer_id.lower().startswith("ai_") or reviewer_id.lower() == "automated":
        raise LedgerError("Human reviewer required. Automated/AI agents cannot review evidence.")
    if not justification:
        raise LedgerError("Review justification is mandatory.")

    ev = get_evidence(evidence_id)
    if not ev:
        raise LedgerError(f"Evidence '{evidence_id}' not found.")

    prev_state = ev["review_state"]
    now_iso = datetime.now(timezone.utc).isoformat()
    review_id = f"rev_ev_{evidence_id}_{int(datetime.now(timezone.utc).timestamp())}"

    with get_db() as conn:
        conn.execute(
            "UPDATE evidence SET review_state = ? WHERE evidence_id = ?;",
            (target_state, evidence_id)
        )
        conn.execute(
            """
            INSERT INTO review_events (
                review_id, record_type, record_id, previous_state, next_state,
                reviewer_id, justification, timestamp, evidence_snapshot_hash
            ) VALUES (?, 'EVIDENCE', ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                review_id, evidence_id, prev_state, target_state,
                reviewer_id, justification, now_iso, ev["provenance_hash"]
            )
        )
    return get_evidence(evidence_id)


def record_contradiction(
    *,
    contradiction_id: str,
    claim_a_id: str,
    conflict_kind: str,
    rationale: str,
    claim_b_id: Optional[str] = None,
    counter_evidence_id: Optional[str] = None,
    state: str = "OPEN",
) -> Dict[str, Any]:
    """Register a disagreement, counter-evidence, or translation difference."""
    if conflict_kind not in ALLOWLISTED_CONFLICT_KINDS:
        raise LedgerError(f"Invalid conflict kind '{conflict_kind}'. Allowed: {sorted(ALLOWLISTED_CONFLICT_KINDS)}")
    if not get_claim(claim_a_id):
        raise LedgerError(f"Claim A '{claim_a_id}' does not exist.")
    if claim_b_id and not get_claim(claim_b_id):
        raise LedgerError(f"Claim B '{claim_b_id}' does not exist.")
    if counter_evidence_id and not get_evidence(counter_evidence_id):
        raise LedgerError(f"Counter evidence '{counter_evidence_id}' does not exist.")

    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO contradictions (
                contradiction_id, claim_a_id, claim_b_id, counter_evidence_id,
                conflict_kind, state, rationale, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(contradiction_id) DO UPDATE SET
                state=excluded.state,
                rationale=excluded.rationale,
                updated_at=excluded.updated_at;
            """,
            (
                contradiction_id, claim_a_id, claim_b_id, counter_evidence_id,
                conflict_kind, state, rationale, now_iso, now_iso
            )
        )
    return get_contradiction(contradiction_id)


def get_contradiction(contradiction_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve contradiction details by contradiction_id."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM contradictions WHERE contradiction_id = ?;", (contradiction_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def promote_claim(
    *,
    claim_id: str,
    target_status: str,
    reviewer_id: str,
    rationale: str,
    clinical_evidence_assessment: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate and promote a claim according to fail-closed promotion rules (G7).

    Must fail-closed with PromotionGateError if:
      1. Reviewer is absent, automated, or AI agent.
      2. Status is SOURCE_SUPPORTED but lacks verified original evidence.
      3. Supporting evidence has not completed human CONTENT/DOMAIN review.
      4. Source locator cannot be resolved or hash verification fails.
      5. Counter-evidence/contradictions are ignored without recorded rationale.
      6. INTERVENTION_EFFECT lacks separate clinical evidence assessment.
    """
    if target_status not in ALLOWLISTED_CLAIM_STATUSES:
        raise PromotionGateError(f"Invalid target status '{target_status}'. Allowed: {sorted(ALLOWLISTED_CLAIM_STATUSES)}")

    # Invariant 1: Reviewer must be human operator
    if not reviewer_id or reviewer_id.lower().startswith("ai_") or reviewer_id.lower() == "automated":
        raise PromotionGateError("Reviewer bypass denied: Claims can only be promoted by a human reviewer.")

    if not rationale:
        raise PromotionGateError("Promotion rationale is mandatory.")

    claim = get_claim(claim_id)
    if not claim:
        raise PromotionGateError(f"Claim '{claim_id}' not found.")

    # Invariant 2: Checks for SOURCE_SUPPORTED
    if target_status == "SOURCE_SUPPORTED":
        linked_ev = claim.get("linked_evidence", [])
        supporting = [e for e in linked_ev if e.get("relation") == "SUPPORTS"]

        if not supporting:
            raise PromotionGateError(
                "INSUFFICIENT_VERIFIED_EVIDENCE: Cannot promote to SOURCE_SUPPORTED without at least one linked supporting evidence."
            )

        # Check evidence review state
        for ev in supporting:
            if ev.get("review_state") not in {"CONTENT_REVIEWED", "DOMAIN_REVIEWED"}:
                raise PromotionGateError(
                    f"INSUFFICIENT_VERIFIED_EVIDENCE: Supporting evidence '{ev['evidence_id']}' has unreviewed state '{ev.get('review_state')}'. Human content review required."
                )

            # Check exact locator resolution and source integrity
            try:
                resolve_source_locator(ev["source_id"], ev["locator_id"])
            except LocatorResolutionError as err:
                raise PromotionGateError(f"SOURCE_UNAVAILABLE: Cannot verify source locator: {err}")

        # Check contradictions and counter-evidence
        contradictions = claim.get("contradictions", [])
        counter_ev = [e for e in linked_ev if e.get("relation") == "CONTRADICTS"]
        if (contradictions or counter_ev) and "CONTRADICTION_ACKNOWLEDGED" not in rationale.upper() and len(rationale) < 15:
            raise PromotionGateError(
                "COUNTER_EVIDENCE_DISCLOSURE_REQUIRED: Claim has open contradictions or counter-evidence. Reviewer must explicitly document counter-evidence resolution in rationale."
            )

        # Invariant for INTERVENTION_EFFECT
        if claim["claim_kind"] == "INTERVENTION_EFFECT":
            if not clinical_evidence_assessment or len(clinical_evidence_assessment.strip()) < 10:
                raise PromotionGateError(
                    "CLINICAL_APPRAISAL_REQUIRED: INTERVENTION_EFFECT claims require explicit clinical evidence assessment detailing study design, population, and confidence."
                )

    now_iso = datetime.now(timezone.utc).isoformat()
    review_id = f"rev_cl_{claim_id}_{int(datetime.now(timezone.utc).timestamp())}"

    with get_db() as conn:
        conn.execute(
            """
            UPDATE claims
            SET status = ?,
                review_state = 'CONTENT_REVIEWED',
                reviewer_id = ?,
                review_rationale = ?,
                clinical_evidence_assessment = ?,
                revised_at = ?
            WHERE claim_id = ?;
            """,
            (target_status, reviewer_id, rationale, clinical_evidence_assessment, now_iso, claim_id)
        )
        conn.execute(
            """
            INSERT INTO review_events (
                review_id, record_type, record_id, previous_state, next_state,
                reviewer_id, justification, timestamp
            ) VALUES (?, 'CLAIM', ?, ?, ?, ?, ?, ?);
            """,
            (
                review_id, claim_id, claim["status"], target_status,
                reviewer_id, rationale, now_iso
            )
        )

    return get_claim(claim_id)


def revise_claim(
    *,
    prior_claim_id: str,
    next_claim_id: str,
    new_statement: str,
    reason: str,
    author_kind: str = "RESEARCHER",
    reviewer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retire a broad or disputed claim and create a narrower successor while preserving lineage."""
    prior = get_claim(prior_claim_id)
    if not prior:
        raise LedgerError(f"Prior claim '{prior_claim_id}' not found.")

    now_iso = datetime.now(timezone.utc).isoformat()
    content_hash = hashlib.sha256(new_statement.encode("utf-8")).hexdigest()

    # 1. Create next claim
    next_claim = create_claim(
        claim_id=next_claim_id,
        statement=new_statement,
        knowledge_namespace=prior["knowledge_namespace"],
        claim_kind=prior["claim_kind"],
        author_kind=author_kind,
        supersedes_claim_id=prior_claim_id,
    )

    # 2. Mark prior claim as REVISED
    with get_db() as conn:
        conn.execute(
            "UPDATE claims SET status = 'REVISED', revised_at = ? WHERE claim_id = ?;",
            (now_iso, prior_claim_id)
        )
        # Record revision event
        event_id = f"rev_evt_{prior_claim_id}_{next_claim_id}"
        conn.execute(
            """
            INSERT INTO claim_revision_events (
                event_id, prior_claim_id, next_claim_id, reason, author_kind, content_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (event_id, prior_claim_id, next_claim_id, reason, author_kind, content_hash, now_iso)
        )

    return get_claim(next_claim_id)


def delete_claim_strictly_forbidden(claim_id: str) -> None:
    """Scholarly Tri-Ledger strictly denies hard deletion of claims."""
    raise DeletionForbiddenError(f"Hard deletion of claim '{claim_id}' is forbidden to preserve scholarly auditability.")
