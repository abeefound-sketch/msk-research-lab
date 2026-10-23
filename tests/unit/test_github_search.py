"""Unit tests for DISC-02 live GitHub search, caching, and candidate persistence."""

import pytest
import json
import httpx
from pathlib import Path
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.discovery.github_search import (
    GitHubSearchQuery,
    GitHubRepoItem,
    search_github,
    save_discovered_candidate,
    compute_transparent_heuristic_score
)


@pytest.fixture
def clean_db(tmp_path):
    db_file = tmp_path / "test_search.sqlite3"
    run_migrations(db_file)
    return db_file


def test_query_string_builder():
    q1 = GitHubSearchQuery(keywords="biomechanics", topic="msk", language="python")
    assert q1.build_query_string() == "biomechanics topic:msk language:python"

    q2 = GitHubSearchQuery(keywords="acupuncture 3d")
    assert q2.build_query_string() == "acupuncture 3d"


def test_transparent_heuristic_score():
    active_repo = {
        "license": {"spdx_id": "MIT"},
        "updated_at": "2026-05-01T00:00:00Z",
        "archived": False,
        "description": "Comprehensive musculoskeletal 3D model viewer and simulator."
    }
    score, breakdown = compute_transparent_heuristic_score(active_repo)
    assert score >= 7.0
    assert "known_open_license" in breakdown
    assert "archived_penalty" not in breakdown

    archived_unlicensed_repo = {
        "license": None,
        "archived": True,
        "description": "Old repo"
    }
    score_arch, breakdown_arch = compute_transparent_heuristic_score(archived_unlicensed_repo)
    assert score_arch == 0.0
    assert "archived_penalty" in breakdown_arch
    assert "unknown_license_penalty" in breakdown_arch


def test_search_github_mock_success_and_cache(clean_db):
    mock_payload = {
        "total_count": 1,
        "items": [
            {
                "name": "open-anatomy-browser",
                "html_url": "https://github.com/openanatomy/open-anatomy-browser",
                "description": "WebGL anatomical visualization platform",
                "language": "JavaScript",
                "stargazers_count": 142,
                "size": 15400,
                "archived": False,
                "updated_at": "2026-08-01T12:00:00Z",
                "license": {"spdx_id": "BSD-3-Clause"},
                "owner": {"login": "openanatomy"}
            }
        ]
    }

    def mock_handler(request):
        return httpx.Response(200, json=mock_payload, headers={"x-ratelimit-remaining": "59"})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=transport)

    query = GitHubSearchQuery(keywords="anatomy webgl")
    result = search_github(query, client=client, custom_db_path=clean_db)

    assert result.status == "OK"
    assert result.total_count == 1
    assert result.is_cached is False
    assert len(result.items) == 1
    assert result.items[0].canonical_url == "https://github.com/openanatomy/open-anatomy-browser"

    # Second call should be served from cache without invoking client
    result_cached = search_github(query, client=None, use_cache=True, custom_db_path=clean_db)
    assert result_cached.is_cached is True
    assert len(result_cached.items) == 1
    assert result_cached.items[0].repo == "open-anatomy-browser"


def test_search_github_rate_limited(clean_db):
    def mock_handler(request):
        return httpx.Response(403, json={"message": "API rate limit exceeded"}, headers={"x-ratelimit-remaining": "0"})

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=transport)

    query = GitHubSearchQuery(keywords="high volume search")
    result = search_github(query, client=client, custom_db_path=clean_db)

    assert result.status == "RATE_LIMITED"
    assert result.rate_limit_remaining == 0
    assert "rate limit exceeded" in result.error_message


def test_search_github_network_offline(clean_db):
    def mock_handler(request):
        raise httpx.ConnectError("Could not connect to api.github.com")

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=transport)

    query = GitHubSearchQuery(keywords="offline test")
    result = search_github(query, client=client, custom_db_path=clean_db)

    assert result.status == "OFFLINE"
    assert "Network unreachable" in result.error_message


def test_save_discovered_candidate(clean_db):
    item = GitHubRepoItem(
        owner="openanatomy",
        repo="open-anatomy-browser",
        canonical_url="https://github.com/openanatomy/open-anatomy-browser",
        description="Atlas browser",
        primary_language="TypeScript",
        license_spdx="BSD-3-Clause",
        stars_count=150,
        heuristic_score=8.5
    )

    cand_id = save_discovered_candidate(item, priority="HIGH", custom_db_path=clean_db)
    assert cand_id == "cand_openanatomy_open-anatomy-browser"

    with get_db(clean_db) as conn:
        cand = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (cand_id,)).fetchone()
        assert cand is not None
        assert cand["status"] == "DISCOVERED_UNVERIFIED"
        assert cand["priority"] == "HIGH"
        assert cand["discovery_source"] == "GITHUB_SEARCH"
        assert cand["stars_count"] == 150
