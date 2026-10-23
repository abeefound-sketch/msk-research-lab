"""Safe repository cloner and SHA verification guard."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.repos.inspector import normalize_repo_url, extract_repo_id


class CloneSecurityError(Exception):
    """Raised on security violation during repository clone."""
    pass


class DirtyCheckoutError(Exception):
    """Raised when an existing checkout has modified/uncommitted work."""
    pass


def get_upstream_repo_dir(repo_id: str) -> Path:
    """Resolve strictly safe path inside 3refs/upstream."""
    cfg = get_config()
    base_dir = cfg.storage.root_dir / cfg.storage.upstream_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    dest = (base_dir / repo_id).resolve()
    # Path traversal check
    if not str(dest).startswith(str(base_dir.resolve())):
        raise CloneSecurityError(f"Target path escapes upstream directory: {dest}")
    return dest


def is_repo_dirty(repo_dir: Path) -> bool:
    """Check if repository has uncommitted or untracked changes."""
    if not (repo_dir / ".git").exists():
        return False
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def get_current_commit_sha(repo_dir: Path) -> Optional[str]:
    """Retrieve current 40-character commit SHA."""
    if not (repo_dir / ".git").exists():
        return None
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5
        )
        sha = res.stdout.strip()
        if len(sha) == 40:
            return sha
    except Exception:
        pass
    return None


def safe_clone(
    url: str,
    target_sha: Optional[str] = None,
    allow_dirty: bool = False
) -> Dict[str, Any]:
    """Clone upstream repository with security invariants.

    1. URL normalized and validated.
    2. Hooks disabled with core.hooksPath=/dev/null.
    3. Destination strictly within 3refs/upstream.
    4. Dirty tree protected.
    5. No build or install scripts executed.
    """
    clean_url = normalize_repo_url(url)
    repo_id = extract_repo_id(clean_url)
    dest_dir = get_upstream_repo_dir(repo_id)

    # Check existing checkout
    if dest_dir.exists():
        if (dest_dir / ".git").exists():
            if is_repo_dirty(dest_dir) and not allow_dirty:
                raise DirtyCheckoutError(f"Checkout at {dest_dir} has local uncommitted changes.")

            curr_sha = get_current_commit_sha(dest_dir)
            if target_sha and curr_sha == target_sha:
                return {
                    "repo_id": repo_id,
                    "path": str(dest_dir),
                    "commit_sha": curr_sha,
                    "action": "ALREADY_AT_TARGET_SHA",
                    "status": "CLONED"
                }

    # Execute safe git clone
    cmd = [
        "git",
        "-c", "core.hooksPath=/dev/null",  # Strict hook execution denial
        "clone",
        "--no-single-branch",
        clean_url,
        str(dest_dir)
    ]

    try:
        if not dest_dir.exists():
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)

        # If a specific target SHA is required, checkout that exact SHA
        if target_sha:
            subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "checkout", target_sha],
                cwd=str(dest_dir),
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

        actual_sha = get_current_commit_sha(dest_dir)

        # Audit event
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (event_type, actor, payload_json)
                VALUES (?, ?, ?);
                """,
                ("REPO_CLONED", "OPERATOR", f'{{"repo_id": "{repo_id}", "sha": "{actual_sha}", "url": "{clean_url}"}}')
            )
            conn.execute(
                """
                UPDATE repositories
                SET pinned_commit_sha = ?, status = 'CLONED_INSPECTABLE', updated_at = (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                WHERE id = ?;
                """,
                (actual_sha, repo_id)
            )

        return {
            "repo_id": repo_id,
            "path": str(dest_dir),
            "commit_sha": actual_sha,
            "action": "CLONED",
            "status": "CLONED_INSPECTABLE"
        }
    except subprocess.CalledProcessError as e:
        raise CloneSecurityError(f"Git clone failed: {e.stderr.strip()}")
