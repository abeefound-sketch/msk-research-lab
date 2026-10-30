"""Asset verification and integrity manifest engine for MSK Research Lab OS."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from msk_research_lab.core.config import get_config

# Standard reference assets bundled or used by MSK Research Lab OS
STANDARD_ASSET_SPEC: Dict[str, Dict[str, Any]] = {
    "watercmy_anatomy_glb": {
        "relative_path": "3refs/upstream/watercmy--anatomy-3d/models/anatomy.glb",
        "description": "Authentic DBCLS BodyParts3D / Z-Anatomy 3D musculoskeletal anatomical mesh",
        "expected_sha256": "318347f91e4989da0c271e9662df536943df1149b413fef01cf21586073ea73e",
        "license": "CC-BY-SA 2.1 JP",
        "critical": True,
    },
    "spacejohnlf_body_glb": {
        "relative_path": "3refs/upstream/spacejohnlf--tcm-acupoints/public/models/body.glb",
        "description": "spacejohnlf Z-Anatomy derived 3D acupuncture mannequin mesh",
        "expected_sha256": "0886b6a068e655b284903664e2178d7964f80b1c0ce798461909ac806bcef2e3",
        "license": "MIT",
        "critical": False,
    },
    "pose_landmarker_lite": {
        "relative_path": "2data/models/pose_landmarker_lite.task",
        "description": "MediaPipe Pose Landmarker Lite neural model for 33 2D/3D pose landmarks",
        "expected_sha256": "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a",
        "license": "Apache 2.0",
        "critical": True,
    },
    "vendor_three_js": {
        "relative_path": "src/msk_research_lab/api/static/vendor/three.min.js",
        "description": "Three.js r128 3D rendering runtime",
        "expected_sha256": "9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2",
        "license": "MIT",
        "critical": True,
    },
    "vendor_gltf_loader": {
        "relative_path": "src/msk_research_lab/api/static/vendor/GLTFLoader.js",
        "description": "Three.js GLTFLoader for parsing binary GLTF / GLB meshes",
        "expected_sha256": "d073b438e6a07e1359741dd5d6c76c953420cc0d4fd84eb1bdde94315540e6a3",
        "license": "MIT",
        "critical": True,
    },
    "vendor_orbit_controls": {
        "relative_path": "src/msk_research_lab/api/static/vendor/OrbitControls.js",
        "description": "Three.js OrbitControls for camera manipulation",
        "expected_sha256": "02bb4ade710f3e607329e37a21f098bc3ac70eb6e33daf8a65e79f4db785e7b2",
        "license": "MIT",
        "critical": True,
    },
}


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file efficiently using 64KB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_asset_manifest(root_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Generate comprehensive asset manifest containing current sizes and computed hashes."""
    if root_dir is None:
        cfg = get_config()
        root_dir = cfg.storage.root_dir

    manifest: Dict[str, Any] = {
        "manifest_version": "1.0.0",
        "generator": "MSK Research Lab Desktop Packaging Engine",
        "assets": {},
    }

    for asset_key, spec in STANDARD_ASSET_SPEC.items():
        file_path = root_dir / spec["relative_path"]
        exists = file_path.exists() and file_path.is_file()
        current_hash = compute_sha256(file_path) if exists else None
        current_size = file_path.stat().st_size if exists else 0

        manifest["assets"][asset_key] = {
            "relative_path": spec["relative_path"],
            "description": spec["description"],
            "license": spec["license"],
            "critical": spec["critical"],
            "exists": exists,
            "size_bytes": current_size,
            "expected_sha256": spec["expected_sha256"],
            "actual_sha256": current_hash,
            "status": "VALID" if current_hash == spec["expected_sha256"] else ("MISSING" if not exists else "MISMATCH"),
        }

    return manifest


def verify_bundled_assets(root_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Verify integrity of all bundled assets against cryptographic expectations."""
    manifest = generate_asset_manifest(root_dir)
    all_valid = True
    critical_valid = True
    mismatches: List[str] = []
    missing: List[str] = []

    for k, item in manifest["assets"].items():
        if item["status"] != "VALID":
            all_valid = False
            if item["status"] == "MISSING":
                missing.append(k)
            else:
                mismatches.append(k)
            if item["critical"]:
                critical_valid = False

    return {
        "all_valid": all_valid,
        "critical_valid": critical_valid,
        "assets_checked": len(manifest["assets"]),
        "missing_assets": missing,
        "mismatched_assets": mismatches,
        "details": manifest["assets"],
    }
