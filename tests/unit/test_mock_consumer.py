"""Unit tests for MSK-Therapy-OS Mock Consumer Client (BRIDGE-01 / BRIDGE-02 / R6)."""

import pytest
import httpx
from pathlib import Path
from msk_research_lab.bridge.packages import create_research_package
from msk_research_lab.bridge.mock_consumer import (
    TherapyResearchClient, AuthenticationError, KnowledgeNotFoundError,
    ConsumerBridgeError, TamperedPackageError
)


@pytest.fixture
def sample_offline_package(tmp_path: Path):
    pkg_dir = tmp_path / "therapy_offline_pkg"
    members = {
        "points/gb21.json": b'{"point_code": "GB21", "canonical_label": "Jianjing", "review_state": "EXPERT_REVIEWED"}'
    }
    create_research_package(
        package_dir=pkg_dir,
        package_id="pkg_therapy_approved_01",
        snapshot_id="snap_20261023_01",
        source_ids=["who_standard_2008"],
        member_contents=members,
        rights_review_state="ALLOWED"
    )
    return pkg_dir


def test_consumer_offline_fallback(sample_offline_package: Path):
    """When Lab OS is offline, consumer retrieves reviewed knowledge from validated package."""
    client = TherapyResearchClient(
        api_base_url="http://127.0.0.1:9999/api/v1", # Unreachable port
        offline_package_dir=sample_offline_package,
        force_offline=True
    )

    data = client.get_point_knowledge("GB21")
    assert data["delivery_channel"] == "OFFLINE_HASHED_PACKAGE"
    assert data["point_code"] == "GB21"
    assert data["canonical_label"] == "Jianjing"
    assert data["package_id"] == "pkg_therapy_approved_01"


def test_consumer_offline_tamper_rejection(sample_offline_package: Path):
    """Tampered offline package fails closed before serving knowledge."""
    # Tamper with file
    f = sample_offline_package / "points" / "gb21.json"
    f.write_bytes(b'{"point_code": "GB21", "TAMPERED": true}')

    client = TherapyResearchClient(
        offline_package_dir=sample_offline_package,
        force_offline=True
    )

    with pytest.raises(TamperedPackageError, match="TAMPERED_PACKAGE_MEMBER"):
        client.get_point_knowledge("GB21")


def test_consumer_offline_unknown_point(sample_offline_package: Path):
    """Unknown point in verified package raises KnowledgeNotFoundError."""
    client = TherapyResearchClient(
        offline_package_dir=sample_offline_package,
        force_offline=True
    )

    with pytest.raises(KnowledgeNotFoundError, match="not included"):
        client.get_point_knowledge("UNKNOWN_POINT_999")
