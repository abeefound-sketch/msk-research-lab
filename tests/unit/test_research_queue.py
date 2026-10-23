"""Unit tests for DISC-03 research queue, state machine, and run gating."""

import pytest
from pathlib import Path
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.discovery.research_queue import (
    update_candidate_state,
    queue_candidate_for_research,
    approve_and_clone_candidate,
    request_run_approval,
    record_research_decision,
    LifecycleTransitionError,
    CloneApprovalError,
    ExecutionBlockedError
)


@pytest.fixture
def clean_db(tmp_path):
    db_file = tmp_path / "test_queue.sqlite3"
    run_migrations(db_file)
    # Seed a candidate
    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO repository_candidates (
                id, canonical_url, owner, repo, status, priority, discovery_source
            ) VALUES (
                'cand_test_repo', 'https://github.com/test-owner/test-repo',
                'test-owner', 'test-repo', 'DISCOVERED_UNVERIFIED', 'MEDIUM', 'MARKDOWN_IMPORT'
            )
            """
        )
    return db_file


def test_update_candidate_state(clean_db):
    update_candidate_state("cand_test_repo", "METADATA_INSPECTED", reason="Manual review", custom_db_path=clean_db)

    with get_db(clean_db) as conn:
        row = conn.execute("SELECT status FROM repository_candidates WHERE id = 'cand_test_repo'").fetchone()
        assert row["status"] == "METADATA_INSPECTED"

    with pytest.raises(LifecycleTransitionError):
        update_candidate_state("cand_test_repo", "INVALID_STATE_NAME", custom_db_path=clean_db)


def test_queue_candidate_for_research(clean_db):
    res = queue_candidate_for_research(
        candidate_id="cand_test_repo",
        priority="HIGH",
        tags=["anatomy", "webgl"],
        research_questions=["Can this render BodyParts3D meshes?"],
        custom_db_path=clean_db
    )

    assert res["status"] == "RESEARCH_QUEUED"
    assert res["priority"] == "HIGH"
    assert len(res["tags"]) == 2

    with get_db(clean_db) as conn:
        row = conn.execute("SELECT status, priority, tags_json FROM repository_candidates WHERE id = 'cand_test_repo'").fetchone()
        assert row["status"] == "RESEARCH_QUEUED"
        assert row["priority"] == "HIGH"
        assert "anatomy" in row["tags_json"]


def test_request_run_approval_fails_closed_when_sandbox_unavailable(clean_db, monkeypatch):
    # Mock probe to return SANDBOX_UNAVAILABLE (matching our WSL host)
    def mock_probe():
        return {
            "status": "SANDBOX_UNAVAILABLE",
            "runtime": None,
            "can_execute_untrusted": False,
            "isolation_enforceable": False,
            "readiness_gate": "BLOCKED",
            "details": "Neither Podman nor Docker runtime detected on this host."
        }

    monkeypatch.setattr("msk_research_lab.discovery.research_queue.probe_sandbox_capabilities", mock_probe)

    with pytest.raises(ExecutionBlockedError) as exc_info:
        request_run_approval(
            candidate_id="cand_test_repo",
            profile_id="default_subproc",
            custom_db_path=clean_db
        )

    assert "SANDBOX_UNAVAILABLE" in str(exc_info.value)

    # Verify candidate state transitioned to BLOCKED
    with get_db(clean_db) as conn:
        row = conn.execute("SELECT status FROM repository_candidates WHERE id = 'cand_test_repo'").fetchone()
        assert row["status"] == "BLOCKED"


def test_record_research_decision(clean_db):
    res = record_research_decision(
        candidate_id="cand_test_repo",
        decision="ADAPT",
        justification="The coordinate transforms in this library can be adapted to our Barycentric mapping.",
        reviewed_by="LEAD_ENGINEER",
        custom_db_path=clean_db
    )

    assert res["decision"] == "ADAPT"
    assert res["reviewed_by"] == "LEAD_ENGINEER"

    with get_db(clean_db) as conn:
        # Check repository_candidates status
        cand = conn.execute("SELECT status FROM repository_candidates WHERE id = 'cand_test_repo'").fetchone()
        assert cand["status"] == "ADAPT"

        # Check research_decisions
        dec = conn.execute("SELECT * FROM research_decisions WHERE candidate_id = 'cand_test_repo'").fetchone()
        assert dec is not None
        assert dec["decision"] == "ADAPT"
        assert "coordinate transforms" in dec["justification"]


def test_record_research_decision_invalid_input(clean_db):
    with pytest.raises(ValueError):
        record_research_decision(
            candidate_id="cand_test_repo",
            decision="INVALID_DECISION",
            justification="Valid justification string",
            custom_db_path=clean_db
        )

    with pytest.raises(ValueError):
        record_research_decision(
            candidate_id="cand_test_repo",
            decision="ADOPT",
            justification="Too short",
            custom_db_path=clean_db
        )
