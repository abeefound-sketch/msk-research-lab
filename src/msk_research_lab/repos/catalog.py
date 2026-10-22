"""Candidate repository catalog and seed loader for R0."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from msk_research_lab.core.db import get_db


def load_catalog_seed(catalog_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load untrusted candidate repos from catalog JSON file."""
    path = catalog_path or Path("config/repo_catalog.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Support both "repositories" (v3 spec) and "candidates" keys
    return data.get("repositories") or data.get("candidates") or []


def seed_repositories_if_empty(catalog_path: Optional[Path] = None) -> int:
    """Seed catalog into database as uninspected candidate records without cloning."""
    candidates = load_catalog_seed(catalog_path)
    if not candidates:
        return 0

    inserted_count = 0
    with get_db() as conn:
        for item in candidates:
            repo_id = item.get("id")
            if not repo_id:
                continue
            cur = conn.execute("SELECT id FROM repositories WHERE id = ?;", (repo_id,))
            if not cur.fetchone():
                url = item.get("url") or item.get("upstream_url") or ""
                name = item.get("github_full_name") or item.get("name") or repo_id
                license_val = item.get("code_license_review") or item.get("license") or "UNKNOWN"
                target_kind = item.get("category") or item.get("target_kind") or "GENERAL_RESEARCH"
                status = item.get("repo_status") or "REGISTERED_UNINSPECTED"

                conn.execute(
                    """
                    INSERT INTO repositories (id, name, upstream_url, license, status, target_kind, catalog_metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        repo_id,
                        name,
                        url,
                        license_val,
                        status,
                        target_kind,
                        json.dumps(item)
                    )
                )
                inserted_count += 1

    return inserted_count


def get_all_repositories() -> List[Dict[str, Any]]:
    """Query all cataloged repositories."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM repositories ORDER BY id ASC;")
        return [dict(row) for row in cur.fetchall()]
