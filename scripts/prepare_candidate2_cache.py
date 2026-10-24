"""Scoped and Verified npm Dependency Staging for Candidate 2 (spacejohnlf/tcm-acupoints).

Strict compliance with Operator Approval:
1. Re-verifies Git commit: 04e35abb66585eb29c7250ea8ab5243c8c744f64.
2. Extracts lockfile-declared packages from package-lock.json.
3. Enforces that all URLs originate from https://registry.npmjs.org/.
4. Downloads each tarball to a dedicated temporary staging folder using parallel workers.
5. Verifies package integrity strictly against lockfile sha512 hashes.
6. Populates a dedicated disposable npm cache using `npm cache add`.
7. Zero execution of install/lifecycle scripts outside sandbox.
"""

import sys
import json
import base64
import hashlib
import urllib.request
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

EXPECTED_COMMIT = "04e35abb66585eb29c7250ea8ab5243c8c744f64"
ALLOWED_REGISTRY = "https://registry.npmjs.org/"

def verify_git_commit(repo_path: Path):
    cmd = ["git", "-C", str(repo_path), "rev-parse", "HEAD"]
    commit = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"Git commit mismatch! Expected {EXPECTED_COMMIT}, found {commit}")
    print(f"[VERIFY] Pinned Git commit matches: {commit}", flush=True)

def download_and_verify(item, staging_dir: Path):
    pkg_path, url, expected_integrity = item
    filename = url.split("/")[-1]
    tarball_path = staging_dir / filename

    if not tarball_path.exists() or tarball_path.stat().st_size == 0:
        req = urllib.request.Request(url, headers={"User-Agent": "MSK-Research-Lab/3.1 (Integrity-Auditor)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(tarball_path, "wb") as f:
            f.write(data)
    else:
        with open(tarball_path, "rb") as f:
            data = f.read()

    # Cryptographic Integrity Check
    if expected_integrity.startswith("sha512-"):
        calc_b64 = "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode("ascii")
        if calc_b64 != expected_integrity:
            tarball_path.unlink(missing_ok=True)
            raise ValueError(
                f"INTEGRITY MISMATCH for {filename}!\nExpected: {expected_integrity}\nComputed: {calc_b64}"
            )
    elif expected_integrity.startswith("sha1-"):
        calc_b64 = "sha1-" + base64.b64encode(hashlib.sha1(data).digest()).decode("ascii")
        if calc_b64 != expected_integrity:
            tarball_path.unlink(missing_ok=True)
            raise ValueError(
                f"INTEGRITY MISMATCH for {filename}!\nExpected: {expected_integrity}\nComputed: {calc_b64}"
            )
    else:
        raise ValueError(f"Unknown integrity format for {filename}: {expected_integrity}")

    return tarball_path

def main():
    repo_path = Path("/mnt/c/Users/tuanh/Downloads/msk-research-lab/3refs/upstream/spacejohnlf--tcm-acupoints")
    verify_git_commit(repo_path)

    lockfile_path = repo_path / "package-lock.json"
    assert lockfile_path.exists(), "package-lock.json not found"

    with open(lockfile_path, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    packages = lock_data.get("packages", {})
    print(f"[VERIFY] Loaded {len(packages)} total entries from package-lock.json", flush=True)

    staging_dir = Path("/tmp/msk-candidate2-tarballs")
    staging_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = Path("/tmp/msk-candidate2-cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    items_to_download = []
    for pkg_path, info in packages.items():
        if not pkg_path:
            continue
        resolved = info.get("resolved")
        integrity = info.get("integrity")
        if not resolved or not integrity:
            continue

        if not resolved.startswith(ALLOWED_REGISTRY):
            raise ValueError(f"SECURITY VIOLATION: Non-official npm URL detected: {resolved}")

        items_to_download.append((pkg_path, resolved, integrity))

    print(f"[PRE-FETCH] Total packages to fetch and verify: {len(items_to_download)} (using 8 parallel workers)", flush=True)

    verified_tarballs = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_and_verify, item, staging_dir): item for item in items_to_download}
        done_count = 0
        for fut in as_completed(futures):
            item = futures[fut]
            try:
                tb = fut.result()
                verified_tarballs.append(tb)
                done_count += 1
                if done_count % 10 == 0 or done_count == len(items_to_download):
                    print(f"[PROGRESS] {done_count}/{len(items_to_download)} packages downloaded & integrity verified.", flush=True)
            except Exception as e:
                print(f"[ERROR] Failed for {item[1]}: {e}", flush=True)
                raise

    print(f"[VERIFY] Successfully downloaded and cryptographically verified {len(verified_tarballs)} tarballs.", flush=True)

    # Populate disposable cache via npm cache add
    print(f"[CACHE] Populating disposable npm cache at {cache_dir}...", flush=True)
    for idx, tb in enumerate(verified_tarballs, 1):
        cmd = [
            "/home/tuan/.nvm/versions/node/v20.20.2/bin/npm",
            "cache", "add",
            "--cache", str(cache_dir),
            str(tb)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to cache {tb.name}: {res.stderr}")
        if idx % 20 == 0 or idx == len(verified_tarballs):
            print(f"[CACHE] {idx}/{len(verified_tarballs)} packages added to cache.", flush=True)

    print(f"[SUCCESS] Candidate 2 dedicated cache populated cleanly at {cache_dir}.", flush=True)

if __name__ == "__main__":
    main()
