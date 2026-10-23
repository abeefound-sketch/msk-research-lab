"""Immutable evidence store, run bundle generator, and SHA-256 verifier."""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class EvidenceBundle:
    """Manages an immutable evidence collection for a specific test/release run."""

    def __init__(self, release_id: str, run_id: Optional[str] = None):
        self.release_id = release_id
        self.run_id = run_id or f"run-{int(time.time())}"
        cfg = get_config()
        self.bundle_dir = cfg.storage.root_dir / cfg.storage.data_dir / "evidence" / release_id / self.run_id
        self.bundle_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts: List[Path] = []

    def record_json(self, name: str, data: Any) -> Path:
        """Write JSON artifact into bundle."""
        target = self.bundle_dir / f"{name}.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.artifacts.append(target)
        return target

    def record_text(self, name: str, text: str) -> Path:
        """Write text/log artifact into bundle."""
        target = self.bundle_dir / name
        with open(target, "w", encoding="utf-8") as f:
            f.write(text)
        self.artifacts.append(target)
        return target

    def finalize(self) -> Dict[str, Any]:
        """Compute SHA-256 manifest of all bundle artifacts and seal the run."""
        manifest = {}
        manifest_lines = []
        for p in sorted(self.artifacts):
            rel_name = p.name
            h = compute_sha256(p)
            manifest[rel_name] = h
            manifest_lines.append(f"{h}  {rel_name}\n")

        manifest_file = self.bundle_dir / "sha256-manifest.txt"
        with open(manifest_file, "w", encoding="utf-8") as f:
            f.writelines(manifest_lines)

        overall_manifest_hash = compute_sha256(manifest_file)

        # Record in database
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence_bundles (id, release_id, bundle_path, artifact_count, manifest_sha256, is_valid)
                VALUES (?, ?, ?, ?, ?, 1);
                """,
                (self.run_id, self.release_id, str(self.bundle_dir), len(self.artifacts), overall_manifest_hash)
            )

        return {
            "run_id": self.run_id,
            "bundle_dir": str(self.bundle_dir),
            "manifest_hash": overall_manifest_hash,
            "artifact_count": len(self.artifacts)
        }


def verify_evidence_bundle(bundle_dir: Path) -> Dict[str, Any]:
    """Verify that none of the artifacts in an evidence bundle have been tampered with."""
    manifest_file = bundle_dir / "sha256-manifest.txt"
    if not manifest_file.exists():
        return {"valid": False, "error": "MISSING_MANIFEST", "mismatches": []}

    mismatches = []
    lines = manifest_file.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        expected_hash, rel_name = parts
        target_file = bundle_dir / rel_name
        if not target_file.exists():
            mismatches.append({"file": rel_name, "error": "FILE_DELETED"})
            continue
        actual_hash = compute_sha256(target_file)
        if actual_hash != expected_hash:
            mismatches.append({
                "file": rel_name,
                "expected": expected_hash,
                "actual": actual_hash,
                "error": "TAMPER_DETECTED"
            })

    return {
        "valid": len(mismatches) == 0,
        "total_files": len(lines),
        "mismatches": mismatches
    }
