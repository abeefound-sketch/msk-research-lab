"""Unit tests for runner safety guard, approvals, and process governor."""

import pytest
from msk_research_lab.repos.runner import (
    approve_run_profile,
    verify_approval,
    governor,
    SandboxExecutionBlockedError
)
from msk_research_lab.core.migrations import run_migrations


def test_approval_lifecycle():
    run_migrations()
    from msk_research_lab.core.db import get_db
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO repositories (id, name, upstream_url) VALUES ('test-repo', 'Test Repo', 'https://github.com/test/repo');")

    token = approve_run_profile("test-repo", "profile-static", "abc1234567890abcdef1234567890abcdef1234")
    assert token.startswith("appr-")

    # Verify matching approval
    assert verify_approval("test-repo", "profile-static", "abc1234567890abcdef1234567890abcdef1234", token) is True

    # Verify wrong token or wrong commit fails
    assert verify_approval("test-repo", "profile-static", "wrong_commit", token) is False
    assert verify_approval("test-repo", "profile-static", "abc1234567890abcdef1234567890abcdef1234", "wrong-token") is False


def test_fail_closed_sandbox_block():
    """Verify that launching non-synthetic untrusted process is BLOCKED when container sandbox is unavailable."""
    with pytest.raises(SandboxExecutionBlockedError):
        governor.launch(
            job_id="untrusted-job-1",
            argv=["echo", "untrusted"],
            cwd=".",
            require_sandbox=True,
            is_synthetic=False
        )
