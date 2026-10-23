"""Persistent Research Queue, State Machine, and Clone Approval Guard (DISC-03)."""

import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.repos.cloner import safe_clone, get_upstream_repo_dir, get_current_commit_sha
from msk_research_lab.sandbox.probe import probe_sandbox_capabilities

VALID_LIFECYCLE_STATES = {
    "DISCOVERED_UNVERIFIED",
    "METADATA_INSPECTED",
    "RESEARCH_QUEUED",
    "STATIC_ANALYZED",
    "CLONE_APPROVAL_PENDING",
    "CLONED_PINNED",
    "RUN_APPROVAL_PENDING",
    "SANDBOX_VERIFIED_RUN",
    "EVALUATED",
    "ADOPT",
    "ADAPT",
    "REJECT",
    "DEFER",
    "BLOCKED",
    "UNSUPPORTED",
    "INCONCLUSIVE",
    "REVIEW_REQUIRED"
}

VALID_DECISIONS = {"ADOPT", "ADAPT", "REJECT", "DEFER"}


class LifecycleTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class CloneApprovalError(Exception):
    """Raised when cloning is attempted without valid operator approval."""
    pass


class ExecutionBlockedError(Exception):
    """Raised when execution approval is denied or sandbox is unavailable."""
    pass


def update_candidate_state(
    candidate_id: str,
    new_state: str,
    reason: Optional[str] = None,
    custom_db_path: Optional[Path] = None
) -> None:
    """Transition candidate to new lifecycle state with audit trail."""
    if new_state not in VALID_LIFECYCLE_STATES:
        raise LifecycleTransitionError(f"Invalid lifecycle state: {new_state}")

    with get_db(custom_db_path) as conn:
        cur = conn.execute("SELECT status FROM repository_candidates WHERE id = ?", (candidate_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(f"Candidate not found: {candidate_id}")

        old_state = row["status"]
        conn.execute(
            """
            UPDATE repository_candidates
            SET status = ?, updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            WHERE id = ?
            """,
            (new_state, candidate_id)
        )

        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "CANDIDATE_STATE_TRANSITION",
                "SYSTEM",
                json.dumps({
                    "candidate_id": candidate_id,
                    "from_state": old_state,
                    "to_state": new_state,
                    "reason": reason or ""
                })
            )
        )


def queue_candidate_for_research(
    candidate_id: str,
    priority: str = "HIGH",
    tags: Optional[List[str]] = None,
    research_questions: Optional[List[str]] = None,
    custom_db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Enroll candidate into persistent research queue."""
    tags = tags or []
    research_questions = research_questions or []

    with get_db(custom_db_path) as conn:
        cur = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (candidate_id,))
        cand = cur.fetchone()
        if not cand:
            raise KeyError(f"Candidate not found: {candidate_id}")

        conn.execute(
            """
            UPDATE repository_candidates
            SET status = 'RESEARCH_QUEUED',
                priority = ?,
                tags_json = ?,
                research_questions_json = ?,
                updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            WHERE id = ?
            """,
            (priority, json.dumps(tags), json.dumps(research_questions), candidate_id)
        )

    return {
        "candidate_id": candidate_id,
        "status": "RESEARCH_QUEUED",
        "priority": priority,
        "tags": tags,
        "research_questions": research_questions
    }


def approve_and_clone_candidate(
    candidate_id: str,
    operator: str,
    pinned_commit_sha: Optional[str] = None,
    custom_db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Explicitly approved, SHA-pinned clone of upstream candidate repository.

    Clone approval is strictly separated from execution approval.
    Hooks disabled (--config core.hooksPath=/dev/null).
    No build, test, or install scripts are executed.
    """
    if not operator or not operator.strip():
        raise CloneApprovalError("Cloning requires explicit operator identity.")

    with get_db(custom_db_path) as conn:
        cur = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (candidate_id,))
        cand = cur.fetchone()
        if not cand:
            raise KeyError(f"Candidate not found: {candidate_id}")

        canonical_url = cand["canonical_url"]

        # Record explicit approval before cloning
        approval_token = f"clone_appr_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "CLONE_EXPLICITLY_APPROVED",
                operator,
                json.dumps({
                    "candidate_id": candidate_id,
                    "url": canonical_url,
                    "target_sha": pinned_commit_sha,
                    "approval_token": approval_token
                })
            )
        )

    # Perform safe clone
    clone_res = safe_clone(
        url=canonical_url,
        target_sha=pinned_commit_sha,
        allow_dirty=False
    )

    actual_sha = clone_res["commit_sha"]
    clone_path = clone_res["path"]

    with get_db(custom_db_path) as conn:
        conn.execute(
            """
            UPDATE repository_candidates
            SET status = 'CLONED_PINNED',
                pinned_commit_sha = ?,
                clone_path = ?,
                updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            WHERE id = ?
            """,
            (actual_sha, clone_path, candidate_id)
        )

    return {
        "candidate_id": candidate_id,
        "status": "CLONED_PINNED",
        "clone_path": clone_path,
        "pinned_commit_sha": actual_sha,
        "operator": operator
    }


def request_run_approval(
    candidate_id: str,
    profile_id: str,
    custom_db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Inspect sandbox capability and attempt run approval.

    Fails closed if safe rootless container/microVM sandbox is unavailable.
    """
    probe = probe_sandbox_capabilities()
    if not probe["can_execute_untrusted"]:
        # Block execution and mark candidate as BLOCKED
        update_candidate_state(
            candidate_id=candidate_id,
            new_state="BLOCKED",
            reason=f"Execution blocked: {probe['details']}",
            custom_db_path=custom_db_path
        )
        raise ExecutionBlockedError(
            f"SANDBOX_UNAVAILABLE: Untrusted code execution is blocked. {probe['details']}"
        )

    # If sandbox was available, transition to RUN_APPROVAL_PENDING
    update_candidate_state(
        candidate_id=candidate_id,
        new_state="RUN_APPROVAL_PENDING",
        reason=f"Sandbox available ({probe['runtime']}). Pending human run authorization.",
        custom_db_path=custom_db_path
    )
    return {
        "candidate_id": candidate_id,
        "status": "RUN_APPROVAL_PENDING",
        "sandbox_runtime": probe["runtime"]
    }


def record_research_decision(
    candidate_id: str,
    decision: str,
    justification: str,
    reviewed_by: str = "OPERATOR",
    custom_db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Record human review decision: ADOPT, ADAPT, REJECT, or DEFER."""
    decision = decision.upper().strip()
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Decision must be one of {VALID_DECISIONS}, got: {decision}")

    if not justification or len(justification.strip()) < 10:
        raise ValueError("A substantive justification (minimum 10 characters) is required.")

    now_iso = datetime.datetime.utcnow().isoformat() + "Z"

    with get_db(custom_db_path) as conn:
        cur = conn.execute("SELECT id FROM repository_candidates WHERE id = ?", (candidate_id,))
        if not cur.fetchone():
            raise KeyError(f"Candidate not found: {candidate_id}")

        conn.execute(
            """
            INSERT INTO research_decisions (
                candidate_id, decision, justification, reviewed_by, reviewed_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, decision, justification, reviewed_by, now_iso)
        )

        conn.execute(
            """
            UPDATE repository_candidates
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (decision, now_iso, candidate_id)
        )

        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "RESEARCH_DECISION_RECORDED",
                reviewed_by,
                json.dumps({
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "justification": justification
                })
            )
        )

    return {
        "candidate_id": candidate_id,
        "decision": decision,
        "justification": justification,
        "reviewed_by": reviewed_by,
        "reviewed_at": now_iso
    }
