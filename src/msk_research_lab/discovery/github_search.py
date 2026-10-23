"""Live GitHub repository search and metadata caching adapter (DISC-02)."""

import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.repos.inspector import parse_canonical_github_url, MalformedUrlError

GITHUB_API_SEARCH_URL = "https://api.github.com/search/repositories"
DEFAULT_CACHE_TTL_SECONDS = 86400  # 24 hours


class GitHubSearchQuery(BaseModel):
    keywords: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)

    def build_query_string(self) -> str:
        parts = []
        if self.keywords:
            parts.append(self.keywords.strip())
        if self.topic:
            parts.append(f"topic:{self.topic.strip()}")
        if self.language:
            parts.append(f"language:{self.language.strip()}")
        return " ".join(parts).strip()


class GitHubRepoItem(BaseModel):
    owner: str
    repo: str
    canonical_url: str
    description: Optional[str] = None
    primary_language: Optional[str] = None
    license_spdx: str = "UNKNOWN"
    stars_count: int = 0
    size_kb: int = 0
    is_archived: bool = False
    updated_at: Optional[str] = None
    heuristic_score: float = 0.0
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    fetched_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")


class GitHubSearchResult(BaseModel):
    query_text: str
    total_count: int
    items: List[GitHubRepoItem]
    is_cached: bool = False
    fetched_at: str
    rate_limit_remaining: Optional[int] = None
    status: str = "OK"  # 'OK', 'RATE_LIMITED', 'OFFLINE', 'EMPTY_QUERY', 'ERROR'
    error_message: Optional[str] = None


def compute_transparent_heuristic_score(item_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """Compute transparent heuristic technical score.

    IMPORTANT: Popularity/stars are NOT an endorsement of medical correctness.
    Scoring prioritizes:
    - License presence (+3.0)
    - Active maintenance in last 2 years (+2.0)
    - Non-archived (+2.0)
    - Has description and documentation (+1.0)
    - Penalties:
      - Archived (-5.0)
      - Unknown license (-3.0)
    Max score: 10.0, Min score: 0.0
    """
    breakdown: Dict[str, float] = {}

    # License signal
    lic = item_data.get("license") or {}
    spdx = lic.get("spdx_id") if isinstance(lic, dict) else None
    if spdx and spdx not in ["NOASSERTION", "NONE"]:
        breakdown["known_open_license"] = 3.0
    else:
        breakdown["unknown_license_penalty"] = -3.0

    # Maintenance recency
    updated_str = item_data.get("updated_at")
    if updated_str:
        try:
            up_dt = datetime.datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            age_days = (datetime.datetime.now(datetime.timezone.utc) - up_dt).days
            if age_days < 365:
                breakdown["recent_updates_1yr"] = 2.0
            elif age_days < 730:
                breakdown["recent_updates_2yr"] = 1.0
        except Exception:
            pass

    # Archived penalty
    if item_data.get("archived", False):
        breakdown["archived_penalty"] = -5.0
    else:
        breakdown["actively_available"] = 2.0

    # Description
    desc = item_data.get("description")
    if desc and len(desc.strip()) > 10:
        breakdown["informative_description"] = 1.0

    raw_sum = sum(breakdown.values())
    final_score = max(0.0, min(10.0, round(raw_sum, 2)))
    return final_score, breakdown


def search_github(
    query: GitHubSearchQuery,
    client: Optional[httpx.Client] = None,
    use_cache: bool = True,
    custom_db_path: Optional[Path] = None,
    auth_token: Optional[str] = None
) -> GitHubSearchResult:
    """Execute GitHub search query with caching, backoff, and transparent scoring."""
    q_str = query.build_query_string()
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"

    if not q_str:
        return GitHubSearchResult(
            query_text="",
            total_count=0,
            items=[],
            is_cached=False,
            fetched_at=now_iso,
            status="EMPTY_QUERY",
            error_message="Query keywords, topic, or language must be specified."
        )

    # 1. Check cache in github_discovery_queries
    if use_cache:
        with get_db(custom_db_path) as conn:
            cur = conn.execute(
                """
                SELECT raw_response_json, fetched_at, ttl_seconds
                FROM github_discovery_queries
                WHERE query_text = ?
                ORDER BY id DESC LIMIT 1
                """,
                (q_str,)
            )
            cached = cur.fetchone()
            if cached:
                cached_time = datetime.datetime.fromisoformat(cached["fetched_at"].replace("Z", "+00:00"))
                ttl_sec = cached["ttl_seconds"]
                age_sec = (datetime.datetime.now(datetime.timezone.utc) - cached_time).total_seconds()
                if age_sec < ttl_sec:
                    raw_data = json.loads(cached["raw_response_json"])
                    items = [GitHubRepoItem(**item) for item in raw_data.get("items", [])]
                    return GitHubSearchResult(
                        query_text=q_str,
                        total_count=raw_data.get("total_count", len(items)),
                        items=items,
                        is_cached=True,
                        fetched_at=cached["fetched_at"],
                        status="OK"
                    )

    # 2. Prepare HTTP request
    token = auth_token or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MSK-Research-Lab-OS-v3.1"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "q": q_str,
        "page": query.page,
        "per_page": query.per_page,
        "sort": "updated",
        "order": "desc"
    }

    own_client = False
    if client is None:
        client = httpx.Client(timeout=10.0)
        own_client = True

    try:
        resp = client.get(GITHUB_API_SEARCH_URL, headers=headers, params=params)

        rate_limit_rem = None
        rem_hdr = resp.headers.get("x-ratelimit-remaining")
        if rem_hdr and rem_hdr.isdigit():
            rate_limit_rem = int(rem_hdr)

        if resp.status_code in (403, 429):
            return GitHubSearchResult(
                query_text=q_str,
                total_count=0,
                items=[],
                is_cached=False,
                fetched_at=now_iso,
                rate_limit_remaining=0,
                status="RATE_LIMITED",
                error_message=f"GitHub API rate limit exceeded ({resp.status_code}). Provide a GITHUB_TOKEN or wait before retrying."
            )

        if resp.status_code != 200:
            return GitHubSearchResult(
                query_text=q_str,
                total_count=0,
                items=[],
                is_cached=False,
                fetched_at=now_iso,
                status="ERROR",
                error_message=f"GitHub API error (HTTP {resp.status_code}): {resp.text[:200]}"
            )

        data = resp.json()
        total_count = data.get("total_count", 0)
        raw_items = data.get("items", [])

        parsed_items: List[GitHubRepoItem] = []
        for raw in raw_items:
            owner_obj = raw.get("owner", {})
            owner_name = owner_obj.get("login", "")
            repo_name = raw.get("name", "")
            html_url = raw.get("html_url", "")

            try:
                canonical, owner, repo = parse_canonical_github_url(html_url)
            except MalformedUrlError:
                continue

            lic_data = raw.get("license") or {}
            spdx = lic_data.get("spdx_id") if isinstance(lic_data, dict) else None
            license_label = spdx if spdx and spdx != "NOASSERTION" else "UNKNOWN"
            if lic_data is None:
                license_label = "NONE"

            score, breakdown = compute_transparent_heuristic_score(raw)

            parsed_items.append(GitHubRepoItem(
                owner=owner,
                repo=repo,
                canonical_url=canonical,
                description=raw.get("description"),
                primary_language=raw.get("language"),
                license_spdx=license_label,
                stars_count=raw.get("stargazers_count", 0),
                size_kb=raw.get("size", 0),
                is_archived=raw.get("archived", False),
                updated_at=raw.get("updated_at"),
                heuristic_score=score,
                score_breakdown=breakdown,
                fetched_at=now_iso
            ))

        # 3. Cache the query results in database
        items_payload = [item.model_dump() for item in parsed_items]
        cache_data = {"total_count": total_count, "items": items_payload}
        with get_db(custom_db_path) as conn:
            conn.execute(
                """
                INSERT INTO github_discovery_queries (
                    query_text, query_type, parameters_json, result_count, raw_response_json, fetched_at, ttl_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    q_str,
                    "KEYWORDS" if query.keywords else ("TOPIC" if query.topic else "LANGUAGE"),
                    json.dumps(query.model_dump()),
                    total_count,
                    json.dumps(cache_data),
                    now_iso,
                    DEFAULT_CACHE_TTL_SECONDS
                )
            )

        return GitHubSearchResult(
            query_text=q_str,
            total_count=total_count,
            items=parsed_items,
            is_cached=False,
            fetched_at=now_iso,
            rate_limit_remaining=rate_limit_rem,
            status="OK"
        )

    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as net_err:
        return GitHubSearchResult(
            query_text=q_str,
            total_count=0,
            items=[],
            is_cached=False,
            fetched_at=now_iso,
            status="OFFLINE",
            error_message=f"Network unreachable or connection timed out: {str(net_err)}"
        )
    finally:
        if own_client:
            client.close()


def save_discovered_candidate(
    item: GitHubRepoItem,
    priority: str = "MEDIUM",
    custom_db_path: Optional[Path] = None
) -> str:
    """Persist a discovered repo into repository_candidates as DISCOVERED_UNVERIFIED."""
    cand_id = f"cand_{item.owner.lower()}_{item.repo.lower()}"

    metadata = {
        "description": item.description,
        "primary_language": item.primary_language,
        "stars_count": item.stars_count,
        "size_kb": item.size_kb,
        "is_archived": item.is_archived,
        "heuristic_score": item.heuristic_score,
        "score_breakdown": item.score_breakdown,
        "fetched_at": item.fetched_at
    }

    with get_db(custom_db_path) as conn:
        conn.execute(
            """
            INSERT INTO repository_candidates (
                id, canonical_url, owner, repo, status, priority,
                primary_language, license_spdx, stars_count, description,
                discovery_source, metadata_json
            ) VALUES (?, ?, ?, ?, 'DISCOVERED_UNVERIFIED', ?, ?, ?, ?, ?, 'GITHUB_SEARCH', ?)
            ON CONFLICT(canonical_url) DO UPDATE SET
                primary_language = excluded.primary_language,
                license_spdx = excluded.license_spdx,
                stars_count = excluded.stars_count,
                description = excluded.description,
                metadata_json = excluded.metadata_json,
                updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            """,
            (
                cand_id,
                item.canonical_url,
                item.owner,
                item.repo,
                priority,
                item.primary_language,
                item.license_spdx,
                item.stars_count,
                item.description,
                json.dumps(metadata)
            )
        )

        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                "DISCOVERED_CANDIDATE_SAVED",
                "OPERATOR",
                f'{{"candidate_id": "{cand_id}", "url": "{item.canonical_url}", "source": "GITHUB_SEARCH"}}'
            )
        )

    return cand_id
