"""Packaging and desktop distribution builder for MSK Research Lab OS."""

import json
import shutil
import sys
from pathlib import Path

from msk_research_lab.core.config import get_config
from msk_research_lab.packaging.asset_verifier import generate_asset_manifest, verify_bundled_assets
from msk_research_lab.packaging.license_notices import write_license_notices_file


def build_desktop_distribution(output_dir: Path) -> dict:
    """Build desktop distribution package layout with launchers, assets, and licenses."""
    cfg = get_config()
    repo_root = cfg.storage.root_dir
    dist_dir = output_dir.resolve()
    dist_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Packaging MSK Research Lab Desktop Workstation to {dist_dir}...")

    # 1. Asset Verification and Manifest
    manifest = generate_asset_manifest(repo_root)
    manifest_file = dist_dir / "ASSET_MANIFEST.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Also write to packaging/
    (repo_root / "packaging" / "ASSET_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[+] Asset manifest written ({len(manifest['assets'])} items)")

    # 2. Third-party License Aggregation
    license_file = dist_dir / "LICENSE_NOTICES.txt"
    write_license_notices_file(license_file)
    write_license_notices_file(repo_root / "packaging" / "LICENSE_NOTICES.txt")
    print(f"[+] License notices compiled ({license_file.stat().st_size} bytes)")

    # 3. Copy Launchers and Control Scripts
    packaging_src = repo_root / "packaging"
    launchers = [
        "MSK-Workstation-Launch.vbs",
        "Stop-MSK-Workstation.bat",
        "rollback_release.bat",
    ]
    for launcher in launchers:
        src = packaging_src / launcher
        if src.exists():
            shutil.copy2(src, dist_dir / launcher)
            print(f"[+] Bundled launcher: {launcher}")

    # Copy start-msk.bat as batch fallback launcher
    start_msk = repo_root / "start-msk.bat"
    if start_msk.exists():
        shutil.copy2(start_msk, dist_dir / "start-msk.bat")
        print("[+] Bundled start-msk.bat")

    # 4. Copy Application Source Tree
    src_target = dist_dir / "src"
    if src_target.exists():
        shutil.rmtree(src_target)
    shutil.copytree(repo_root / "src", src_target)
    print(f"[+] Bundled application source tree: {src_target}")

    # 5. Copy Models Directory (including atlas subdirectory with 3D assemblies and validation datasets)
    models_target = dist_dir / "2data" / "models"
    if models_target.exists():
        shutil.rmtree(models_target)
    shutil.copytree(repo_root / "2data" / "models", models_target)
    print(f"[+] Bundled complete neural models and atlas assets tree: {models_target}")

    # 6. Copy Upstream 3D Models
    upstream_3d = dist_dir / "3refs" / "upstream"
    upstream_3d.mkdir(parents=True, exist_ok=True)
    # watercmy
    watercmy_src = repo_root / "3refs" / "upstream" / "watercmy--anatomy-3d" / "models" / "anatomy.glb"
    if watercmy_src.exists():
        watercmy_dest = upstream_3d / "watercmy--anatomy-3d" / "models"
        watercmy_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(watercmy_src, watercmy_dest / "anatomy.glb")
        print("[+] Bundled watercmy anatomy.glb")

    # spacejohnlf
    spacejohnlf_src = repo_root / "3refs" / "upstream" / "spacejohnlf--tcm-acupoints" / "public" / "models" / "body.glb"
    if spacejohnlf_src.exists():
        spacejohnlf_dest = upstream_3d / "spacejohnlf--tcm-acupoints" / "public" / "models"
        spacejohnlf_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(spacejohnlf_src, spacejohnlf_dest / "body.glb")
        print("[+] Bundled spacejohnlf body.glb")

    # 7. Verify package integrity
    verify_res = verify_bundled_assets(dist_dir)
    print(f"[*] Package verification status: critical_valid={verify_res['critical_valid']}")

    summary = {
        "dist_path": str(dist_dir),
        "manifest_assets": len(manifest["assets"]),
        "verification": verify_res,
        "launchers": launchers,
    }
    return summary


if __name__ == "__main__":
    out = Path("dist/MSK-Workstation")
    res = build_desktop_distribution(out)
    print("\nPackage Summary:")
    print(json.dumps(res, indent=2))
