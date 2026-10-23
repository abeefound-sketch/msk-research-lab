"""Unit tests for Offline Approved Research Package Generator & Validator (BRIDGE-02 / R6)."""

import pytest
from pathlib import Path
from msk_research_lab.bridge.packages import (
    create_research_package, validate_offline_package,
    TamperedPackageError, PackageRightsError, PackageSecurityError
)


def test_create_and_validate_offline_package(tmp_path: Path):
    pkg_dir = tmp_path / "pkg_test_01"
    members = {
        "points/gb21.json": b'{"point_code": "GB21", "canonical_label": "Jianjing"}',
        "citations/c1.json": b'{"citation_id": "c1", "source": "who_2008"}'
    }

    manifest = create_research_package(
        package_dir=pkg_dir,
        package_id="pkg_test_01",
        snapshot_id="snap_20261023_01",
        source_ids=["who_2008"],
        member_contents=members,
        rights_review_state="ALLOWED"
    )

    assert manifest["schema_version"] == "3.0.0"
    assert manifest["package_id"] == "pkg_test_01"
    assert len(manifest["members"]) == 2
    assert "manifest_sha256" in manifest

    # Validate package
    val = validate_offline_package(pkg_dir)
    assert val["status"] == "VALID"
    assert val["verified_members_count"] == 2


def test_tampered_package_member_rejected(tmp_path: Path):
    pkg_dir = tmp_path / "pkg_tampered"
    members = {
        "points/gb21.json": b'{"point_code": "GB21", "canonical_label": "Jianjing"}'
    }

    create_research_package(
        package_dir=pkg_dir,
        package_id="pkg_tampered",
        snapshot_id="snap_01",
        source_ids=["who_2008"],
        member_contents=members,
        rights_review_state="ALLOWED"
    )

    # Tamper with file on disk
    target_file = pkg_dir / "points" / "gb21.json"
    target_file.write_bytes(b'{"point_code": "GB21", "MALICIOUS_INJECTION": true}')

    # Validation must fail closed
    with pytest.raises(TamperedPackageError, match="TAMPERED_PACKAGE_MEMBER"):
        validate_offline_package(pkg_dir)


def test_path_traversal_rejected(tmp_path: Path):
    pkg_dir = tmp_path / "pkg_traversal"
    members = {
        "../escape/passwd": b"root:x:0:0..."
    }

    with pytest.raises(PackageSecurityError, match="PATH_TRAVERSAL_DETECTED"):
        create_research_package(
            package_dir=pkg_dir,
            package_id="pkg_traversal",
            snapshot_id="snap_01",
            source_ids=["who_2008"],
            member_contents=members,
            rights_review_state="ALLOWED"
        )


def test_unapproved_rights_rejected(tmp_path: Path):
    pkg_dir = tmp_path / "pkg_bad_rights"
    members = {"doc.txt": b"content"}

    with pytest.raises(PackageRightsError, match="Must be 'ALLOWED'"):
        create_research_package(
            package_dir=pkg_dir,
            package_id="pkg_bad_rights",
            snapshot_id="snap_01",
            source_ids=["src_1"],
            member_contents=members,
            rights_review_state="REVIEW_REQUIRED"
        )
