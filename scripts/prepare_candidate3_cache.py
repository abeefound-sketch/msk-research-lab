"""Scoped and Verified npm Dependency Staging for Candidate 3 (JICio/tcm-3d).

Strict compliance with Operator Approval:
1. Re-verifies Git commit: e8b9ad1c17e67a25e94406100e3fb5c296c24f7a.
2. Extracts lockfile-declared packages from package-lock.json.
3. Enforces that all URLs originate from https://registry.npmjs.org/.
4. Populates a dedicated disposable npm cache using `npm cache add <url>`.
5. Zero execution of install/lifecycle scripts outside sandbox.
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

EXPECTED_COMMIT = "e8b9ad1c17e67a25e94406100e3fb5c296c24f7a"
ALLOWED_REGISTRY = "https://registry.npmjs.org/"

def verify_git_commit(repo_path: Path):
    cmd = ["git", "-C", str(repo_path), "rev-parse", "HEAD"]
    commit = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"Git commit mismatch! Expected {EXPECTED_COMMIT}, found {commit}")
    print(f"[VERIFY] Pinned Git commit matches: {commit}", flush=True)

def cache_package_url(url: str, cache_dir: Path):
    cmd = [
        "/home/tuan/.nvm/versions/node/v20.20.2/bin/npm",
        "cache", "add",
        "--cache", str(cache_dir),
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to cache {url}: {res.stderr}")
    return url

def main():
    repo_path = Path("/mnt/c/Users/tuanh/Downloads/msk-research-lab/3refs/upstream/jicio--tcm-3d")
    verify_git_commit(repo_path)

    lockfile_path = repo_path / "package-lock.json"
    assert lockfile_path.exists(), "package-lock.json not found"

    with open(lockfile_path, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    packages = lock_data.get("packages", {})
    print(f"[VERIFY] Loaded {len(packages)} total entries from package-lock.json", flush=True)

    cache_dir = Path("/tmp/msk-candidate3-cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    urls_to_cache = []
    seen = set()
    for pkg_path, info in packages.items():
        if not pkg_path:
            continue
        resolved = info.get("resolved")
        if not resolved:
            continue

        if not resolved.startswith(ALLOWED_REGISTRY):
            raise ValueError(f"SECURITY VIOLATION: Non-official npm URL detected: {resolved}")

        if resolved not in seen:
            seen.add(resolved)
            urls_to_cache.append(resolved)

    print(f"[PRE-FETCH] Total distinct URLs to cache: {len(urls_to_cache)} (using 16 parallel workers)", flush=True)

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(cache_package_url, u, cache_dir): u for u in urls_to_cache}
        done_count = 0
        for fut in as_completed(futures):
            u = futures[fut]
            try:
                fut.result()
                done_count += 1
                if done_count % 50 == 0 or done_count == len(urls_to_cache):
                    print(f"[CACHE] {done_count}/{len(urls_to_cache)} packages cached by URL.", flush=True)
            except Exception as e:
                print(f"[ERROR] Failed for {u}: {e}", flush=True)
                raise

    print(f"[SUCCESS] Candidate 3 dedicated cache populated cleanly at {cache_dir}.", flush=True)

if __name__ == "__main__":
    main()
