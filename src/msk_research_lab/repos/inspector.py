"""Static repository inspector, URL normalizer, and license/rights analyzer."""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse


DANGEROUS_CHARS = re.compile(r"[;&|`$<>\r\n\t]")
GITHUB_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


class MalformedUrlError(ValueError):
    """Raised when repository URL contains malicious or invalid syntax."""
    pass


def normalize_repo_url(url: str) -> str:
    """Normalize and strictly validate repository URL.

    Rejects file://, javascript:, credentials, shell metacharacters, and malformed targets.
    Tolerates and strips query strings and fragments.
    """
    if not url or not isinstance(url, str):
        raise MalformedUrlError("Repository URL must be a non-empty string.")

    url = url.strip()

    # Reject shell injection characters and unprintable whitespace
    if DANGEROUS_CHARS.search(url):
        raise MalformedUrlError(f"Rejected dangerous characters in URL: {url}")

    # Handle git@github.com:owner/repo pattern before urlparse
    if url.startswith("git@github.com:"):
        clean_path = url[len("git@github.com:"):]
        url = "https://github.com/" + clean_path

    parsed = urlparse(url)

    # Reject local file schemes or script execution
    if parsed.scheme in ["file", "javascript", "data", "ftp"]:
        raise MalformedUrlError(f"Forbidden URL scheme: {parsed.scheme}")

    if parsed.scheme not in ["http", "https"]:
        raise MalformedUrlError(f"Unsupported scheme: {parsed.scheme}")

    # Reject credentials embedded in authority (e.g. user:pass@host)
    if parsed.username or parsed.password or "@" in parsed.netloc:
        raise MalformedUrlError("URL must not contain embedded user credentials.")

    # Validate hostname
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise MalformedUrlError("URL missing hostname.")

    # Reject deceptive lookalike hostnames (e.g. github.com.attacker.com, evil-github.com)
    if ("github.com" in hostname or "github" in hostname) and hostname not in ["github.com", "www.github.com"]:
        raise MalformedUrlError(f"Rejected deceptive GitHub lookalike hostname: {hostname}")

    # Disallow path traversal
    path_segments = [seg for seg in parsed.path.strip("/").split("/") if seg]
    for seg in path_segments:
        if seg in [".", ".."]:
            raise MalformedUrlError("URL path contains path traversal segments.")

    if not path_segments:
        raise MalformedUrlError("URL path has no repository segments.")

    # Normalize path: strip .git suffix if present
    normalized_path = "/" + "/".join(path_segments)
    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]

    # Reassemble clean URL without query parameters or fragment
    clean = f"{parsed.scheme}://{parsed.netloc}{normalized_path}"
    return clean


def parse_canonical_github_url(url: str) -> Tuple[str, str, str]:
    """Parse and validate canonical GitHub repository root (https://github.com/{owner}/{repo}).

    Returns:
        (canonical_url, owner, repo)

    Raises:
        MalformedUrlError if URL is not a valid canonical GitHub repository root.
    """
    clean_url = normalize_repo_url(url)
    parsed = urlparse(clean_url)
    hostname = (parsed.hostname or "").lower()

    if hostname not in ["github.com", "www.github.com"]:
        raise MalformedUrlError(f"Host must be github.com, got: {hostname}")

    segments = [s for s in parsed.path.strip("/").split("/") if s]
    if len(segments) != 2:
        raise MalformedUrlError(f"Canonical GitHub repo requires exactly owner and repo segments, got {segments}")

    owner, repo = segments[0], segments[1]
    if not GITHUB_IDENTIFIER.match(owner) or not GITHUB_IDENTIFIER.match(repo):
        raise MalformedUrlError(f"Invalid owner or repo identifier: {owner}/{repo}")

    canonical_url = f"https://github.com/{owner}/{repo}"
    return canonical_url, owner, repo



def extract_repo_id(normalized_url: str) -> str:
    """Derive canonical identifier from repository URL."""
    clean = normalized_url.rstrip("/")
    parts = clean.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}--{parts[-1]}".lower()
    return clean.replace("/", "--").lower()


def detect_licenses_in_directory(repo_dir: Path) -> Dict[str, str]:
    """Scan directory for LICENSE files and common headers statically."""
    results = {
        "code_license": "UNKNOWN",
        "asset_license": "UNKNOWN",
        "data_license": "UNKNOWN",
        "copyleft_risk": "NONE",
        "notes": ""
    }

    if not repo_dir.exists():
        return results

    license_files = list(repo_dir.glob("LICENSE*")) + list(repo_dir.glob("COPYING*"))
    for lf in license_files:
        try:
            content = lf.read_text(encoding="utf-8", errors="ignore")
            content_upper = content.upper()

            if "AGPL" in content_upper or "AFFERO GENERAL PUBLIC LICENSE" in content_upper:
                results["code_license"] = "AGPL-3.0"
                results["copyleft_risk"] = "HIGH"
                results["notes"] = "AGPL-3.0 detected: Network copyleft requires isolation; do not bundle into core server."
                break
            elif "APACHE" in content_upper:
                results["code_license"] = "Apache-2.0"
            elif "MIT" in content_upper:
                results["code_license"] = "MIT"
            elif "GPL" in content_upper:
                results["code_license"] = "GPL-3.0"
                results["copyleft_risk"] = "MEDIUM"
            elif "CREATIVE COMMONS" in content_upper or "CC BY" in content_upper:
                results["asset_license"] = "CC-BY-4.0"
        except Exception:
            pass

    # Check for 3D model files (GLB, OBJ, STL) which often carry separate asset terms
    models = list(repo_dir.glob("**/*.glb")) + list(repo_dir.glob("**/*.gltf")) + list(repo_dir.glob("**/*.obj"))
    if models:
        results["asset_license"] = "REVIEW_REQUIRED (3D Model Assets Present)"
        if not results["notes"]:
            results["notes"] = f"Found {len(models)} 3D model asset(s). Asset license must be audited separately from code."

    return results


def inspect_repository(repo_dir: Path, repo_id: str, commit_sha: Optional[str] = None) -> Dict[str, Any]:
    """Perform static security and rights inspection of a repository."""
    licenses = detect_licenses_in_directory(repo_dir)

    dependencies = []
    # Check package.json
    pkg_json = repo_dir / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                deps = list(data.get("dependencies", {}).keys())
                dependencies.extend([f"npm:{d}" for d in deps])
        except Exception:
            pass

    # Check requirements.txt
    req_txt = repo_dir / "requirements.txt"
    if req_txt.exists():
        try:
            lines = req_txt.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.append(f"pypi:{line.split('==')[0].split('>=')[0].strip()}")
        except Exception:
            pass

    # Risk evaluation
    risk_flags = []
    if licenses["copyleft_risk"] == "HIGH":
        risk_flags.append("RISK_AGPL_COPYLEFT")
    if licenses["code_license"] == "UNKNOWN":
        risk_flags.append("RISK_UNKNOWN_CODE_LICENSE")
    if "REVIEW_REQUIRED" in licenses["asset_license"]:
        risk_flags.append("RISK_SEPARATE_ASSET_TERMS")

    return {
        "repo_id": repo_id,
        "commit_sha": commit_sha,
        "code_license": licenses["code_license"],
        "asset_license": licenses["asset_license"],
        "data_license": licenses["data_license"],
        "copyleft_risk": licenses["copyleft_risk"],
        "dependencies": dependencies,
        "risk_flags": risk_flags,
        "notes": licenses["notes"],
        "inspection_status": "INSPECTED"
    }
