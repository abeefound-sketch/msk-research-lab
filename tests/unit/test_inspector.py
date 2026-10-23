"""Unit tests for URL normalization and static repository inspection."""

import pytest
import tempfile
from pathlib import Path
from msk_research_lab.repos.inspector import (
    normalize_repo_url,
    extract_repo_id,
    detect_licenses_in_directory,
    inspect_repository,
    MalformedUrlError
)


def test_url_normalization_positive():
    assert normalize_repo_url("https://github.com/openanatomy/open-anatomy-browser.git/") == "https://github.com/openanatomy/open-anatomy-browser"
    assert normalize_repo_url("git@github.com:JICio/tcm-3d.git") == "https://github.com/JICio/tcm-3d"
    assert normalize_repo_url("http://github.com/WaterCMY/anatomy-3d") == "http://github.com/WaterCMY/anatomy-3d"


def test_url_normalization_negatives():
    with pytest.raises(MalformedUrlError):
        normalize_repo_url("javascript:alert(1)")

    with pytest.raises(MalformedUrlError):
        normalize_repo_url("file:///etc/passwd")

    with pytest.raises(MalformedUrlError):
        normalize_repo_url("https://github.com/test;rm -rf /")

    with pytest.raises(MalformedUrlError):
        normalize_repo_url("https://github.com/`touch /tmp/pwn`")


def test_extract_repo_id():
    assert extract_repo_id("https://github.com/JICio/tcm-3d") == "jicio--tcm-3d"


def test_detect_licenses_mit_and_agpl():
    with tempfile.TemporaryDirectory() as tmp_dir:
        d = Path(tmp_dir)

        # 1. MIT test
        (d / "LICENSE").write_text("MIT License Copyright (c) 2026", encoding="utf-8")
        lic = detect_licenses_in_directory(d)
        assert lic["code_license"] == "MIT"
        assert lic["copyleft_risk"] == "NONE"

        # 2. AGPL test
        (d / "LICENSE").write_text("GNU AFFERO GENERAL PUBLIC LICENSE Version 3 (AGPL)", encoding="utf-8")
        lic_agpl = detect_licenses_in_directory(d)
        assert lic_agpl["code_license"] == "AGPL-3.0"
        assert lic_agpl["copyleft_risk"] == "HIGH"
        assert "AGPL-3.0 detected" in lic_agpl["notes"]


def test_detect_separate_asset_license():
    with tempfile.TemporaryDirectory() as tmp_dir:
        d = Path(tmp_dir)
        (d / "LICENSE").write_text("MIT License", encoding="utf-8")
        # Create a 3D model asset
        (d / "model.glb").write_bytes(b"dummy glb bytes")

        lic = detect_licenses_in_directory(d)
        assert lic["code_license"] == "MIT"
        assert "REVIEW_REQUIRED" in lic["asset_license"]
