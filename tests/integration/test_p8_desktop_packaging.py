"""Tests for P8-A Native Desktop Packaging, asset manifest, and licenses."""

import json
from pathlib import Path
import pytest
from msk_research_lab.core.config import AppConfig, get_config, get_desktop_user_data_dir
from msk_research_lab.packaging.asset_verifier import (
    STANDARD_ASSET_SPEC,
    compute_sha256,
    generate_asset_manifest,
    verify_bundled_assets,
)
from msk_research_lab.packaging.license_notices import (
    THIRD_PARTY_LICENSES,
    format_license_notices,
    write_license_notices_file,
)


def test_desktop_user_data_dir_resolution(monkeypatch, tmp_path):
    """Verify desktop user data directory resolution handles environment properly."""
    fake_appdata = tmp_path / "AppData" / "Local"
    monkeypatch.setenv("LOCALAPPDATA", str(fake_appdata))
    d = get_desktop_user_data_dir()
    assert "MSKResearchLab" in str(d)
    assert str(fake_appdata) in str(d)


def test_storage_mode_desktop(monkeypatch, tmp_path):
    """Verify MSK_STORAGE_MODE=desktop redirects storage data and db path to user directory."""
    fake_localappdata = tmp_path / "AppData" / "Local"
    monkeypatch.setenv("LOCALAPPDATA", str(fake_localappdata))
    monkeypatch.setenv("MSK_STORAGE_MODE", "desktop")

    cfg = AppConfig.load()
    assert "MSKResearchLab" in str(cfg.storage.data_dir)
    assert str(cfg.storage.db_path).endswith("lab.sqlite3")
    assert "MSKResearchLab" in str(cfg.storage.db_path)


def test_standard_asset_manifest_and_verification():
    """Verify asset verification identifies bundled models and frontend libraries."""
    manifest = generate_asset_manifest()
    assert "manifest_version" in manifest
    assert "watercmy_anatomy_glb" in manifest["assets"]
    assert "pose_landmarker_lite" in manifest["assets"]
    assert "vendor_three_js" in manifest["assets"]

    res = verify_bundled_assets()
    assert res["critical_valid"] is True, f"Critical assets invalid: {res['missing_assets']} {res['mismatched_assets']}"
    assert res["assets_checked"] >= 6


def test_license_notices_generation(tmp_path):
    """Verify third-party license notices compilation."""
    out_file = tmp_path / "LICENSE_NOTICES.txt"
    written = write_license_notices_file(out_file)
    assert written.exists()

    content = written.read_text(encoding="utf-8")
    assert "MSK RESEARCH LAB OS" in content
    assert "BodyParts3D" in content
    assert "CC BY-SA 2.1 JP" in content
    assert "Google LLC" in content
    assert "Three.js Authors" in content
    assert "Apache License 2.0" in content
    assert "MIT License" in content
