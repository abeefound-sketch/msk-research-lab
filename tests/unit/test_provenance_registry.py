"""Unit tests for Source Provenance Registry and Locator Resolution (G8 / R3-01, R3-04)."""

import hashlib
import tempfile
from pathlib import Path
import pytest

from msk_research_lab.core.config import get_config
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.provenance.registry import (
    register_source,
    get_source,
    register_source_location,
    get_source_location,
    register_source_relation,
    check_source_independence,
    resolve_source_locator,
    ProvenanceError,
    LocatorResolutionError,
)


@pytest.fixture(autouse=True)
def setup_db():
    run_migrations()


def test_register_and_get_source():
    src = register_source(
        source_id="src:textbook:atlas_01",
        kind="TEXTBOOK",
        canonical_uri="file:///data/originals/atlas_01.pdf",
        title="Comprehensive MSK Anatomy Atlas",
        author="Prof. H. Anatomist",
        language="en",
        edition_id="ed_2021",
        rights_status="RESTRICTED",
        independence_group_id="group_anatomist_2021",
    )
    assert src["source_id"] == "src:textbook:atlas_01"
    assert src["title"] == "Comprehensive MSK Anatomy Atlas"
    assert src["rights_status"] == "RESTRICTED"

    fetched = get_source("src:textbook:atlas_01")
    assert fetched is not None
    assert fetched["author"] == "Prof. H. Anatomist"


def test_register_invalid_source_kind_or_rights():
    with pytest.raises(ProvenanceError, match="Invalid source kind"):
        register_source(
            source_id="src:bad:01",
            kind="NON_EXISTENT_KIND",
            canonical_uri="uri://test",
            title="Bad",
        )

    with pytest.raises(ProvenanceError, match="Invalid rights status"):
        register_source(
            source_id="src:bad:02",
            kind="TEXTBOOK",
            canonical_uri="uri://test",
            title="Bad Rights",
            rights_status="FREELY_DISTRIBUTABLE_WITHOUT_LICENSE",
        )


def test_source_independence_tracking():
    # Source A and B share independence group (e.g. translation or derivation)
    register_source(
        source_id="src:who:standard_en",
        kind="CLINICAL_GUIDELINE",
        canonical_uri="https://who.int/acupuncture_en.pdf",
        title="WHO Standard Acupuncture Nomenclature (EN)",
        independence_group_id="who_standard_nomenclature",
    )
    register_source(
        source_id="src:who:standard_vi",
        kind="CLINICAL_GUIDELINE",
        canonical_uri="https://who.int/acupuncture_vi.pdf",
        title="WHO Standard Acupuncture Nomenclature (VI)",
        independence_group_id="who_standard_nomenclature",
    )
    register_source(
        source_id="src:vietnam:truyen_thong",
        kind="TRADITIONAL_PRIMARY_TEXT",
        canonical_uri="file:///refs/truyen_thong.epub",
        title="Châm Cứu Cổ Truyền Việt Nam",
        independence_group_id="vietnam_traditional_acupuncture",
    )

    # 1. Same group -> Not independent
    check_shared = check_source_independence("src:who:standard_en", "src:who:standard_vi")
    assert check_shared["is_independent"] is False
    assert "SHARED_INDEPENDENCE_GROUP" in check_shared["reason"]

    # 2. Distinct groups -> Independent
    check_distinct = check_source_independence("src:who:standard_en", "src:vietnam:truyen_thong")
    assert check_distinct["is_independent"] is True
    assert check_distinct["reason"] == "DISTINCT_PROVENANCE_GROUPS"

    # 3. Explicit relation DERIVED_FROM -> Not independent
    register_source(
        source_id="src:mirror:who_clone",
        kind="REPO_DOCUMENTATION",
        canonical_uri="https://github.com/example/who-mirror",
        title="Unofficial WHO Points Repo",
        independence_group_id="mirror_project_99",
    )
    register_source_relation(
        relation_id="rel_mirror_001",
        source_a_id="src:mirror:who_clone",
        source_b_id="src:who:standard_en",
        kind="DERIVED_FROM",
        rationale="Scraped from WHO standard nomenclature document",
    )
    check_derived = check_source_independence("src:mirror:who_clone", "src:who:standard_en")
    assert check_derived["is_independent"] is False
    assert "DECLARED_RELATION:DERIVED_FROM" in check_derived["reason"]


def test_locator_resolution_positive_and_negative():
    cfg = get_config()
    # Create synthetic original file in 2data/originals
    content = b"PDF-1.4 Exact Page 42 Content for Acupoint GB21"
    content_sha = hashlib.sha256(content).hexdigest()

    orig_dir = cfg.data_dir / "originals" / content_sha
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_file = orig_dir / "content"
    orig_file.write_bytes(content)

    register_source(
        source_id="src:doc:gb21_atlas",
        kind="TEXTBOOK",
        canonical_uri=str(orig_file),
        title="Atlas of Surface Acupuncture",
        sha256=content_sha,
    )
    register_source_location(
        locator_id="loc:pdf:p42",
        source_id="src:doc:gb21_atlas",
        locator_type="PDF_PAGE",
        locator_details={"page": 42, "region": [0.1, 0.2, 0.5, 0.4]},
    )

    # 1. Positive resolution
    res = resolve_source_locator("src:doc:gb21_atlas", "loc:pdf:p42")
    assert res["status"] == "RESOLVED"
    assert res["locator_details"]["page"] == 42

    # 2. Negative: Invalid locator bounds (page 0)
    register_source_location(
        locator_id="loc:pdf:bad_page",
        source_id="src:doc:gb21_atlas",
        locator_type="PDF_PAGE",
        locator_details={"page": 0},
    )
    with pytest.raises(LocatorResolutionError, match="INVALID_LOCATOR"):
        resolve_source_locator("src:doc:gb21_atlas", "loc:pdf:bad_page")

    # 3. Negative: Tampered file content (hash mismatch)
    orig_file.write_bytes(b"TAMPERED CONTENT IN ORIGINAL STORE")
    try:
        with pytest.raises(LocatorResolutionError, match="HASH_MISMATCH"):
            resolve_source_locator("src:doc:gb21_atlas", "loc:pdf:p42")
    finally:
        # Restore clean content
        orig_file.write_bytes(content)
