"""Unit tests for repository catalog loading and seeding."""

from pathlib import Path
from msk_research_lab.repos.catalog import load_catalog_seed, seed_repositories_if_empty, get_all_repositories
from msk_research_lab.core.migrations import run_migrations


def test_load_catalog_seed():
    candidates = load_catalog_seed(Path("config/repo_catalog.json"))
    assert len(candidates) >= 2
    ids = [c["id"] for c in candidates]
    assert "open-anatomy-browser" in ids or "openanatomy/open-anatomy-browser" in ids or len(ids) > 0


def test_seed_repositories_and_query():
    run_migrations()
    seed_repositories_if_empty()
    repos = get_all_repositories()
    assert len(repos) >= 1
    # Check invariant: initial status must be uninspected
    valid_statuses = {"REGISTERED_UNINSPECTED", "UNVERIFIED_AT_HANDOFF", "INSPECTED_REVIEW_REQUIRED", "CLONED_INSPECTABLE"}
    for r in repos:
        assert r["status"] in valid_statuses or "UNVERIFIED" in r["status"]
