"""Unit tests for Side-by-Side Comparator and Epistemic Geometry Guard (G8 / R3-04)."""

import pytest
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.provenance.registry import (
    register_source,
    register_source_location,
)
from msk_research_lab.provenance.comparator import compare_sources, get_comparison, ComparisonError


@pytest.fixture(autouse=True)
def setup_comparator_db():
    run_migrations()


def test_textual_source_comparison():
    register_source(
        source_id="src:book:edition_1985",
        kind="TEXTBOOK",
        canonical_uri="file:///refs/ed_1985.pdf",
        title="Classical Point Locations (1985 Edition)",
    )
    register_source(
        source_id="src:book:edition_2010",
        kind="TEXTBOOK",
        canonical_uri="file:///refs/ed_2010.pdf",
        title="Modern Point Locations (2010 Edition)",
    )

    cmp_res = compare_sources(
        comparison_id="cmp_text_001",
        source_a_id="src:book:edition_1985",
        source_b_id="src:book:edition_2010",
        classification="MATCH",
        operator_notes="Both editions agree on C7-acromion midpoint reference.",
        is_geometric=False,
    )
    assert cmp_res["comparison_id"] == "cmp_text_001"
    assert cmp_res["classification"] == "MATCH"
    assert cmp_res["geometric_comparability_state"] == "TEXTUAL_NON_GEOMETRIC"


def test_geometric_comparison_epistemic_guard():
    register_source(
        source_id="src:mesh:repo_a",
        kind="REPO_SOURCE_CODE",
        canonical_uri="https://github.com/example/model_a",
        title="Repo A 3D Body Mesh",
    )
    register_source(
        source_id="src:mesh:repo_b",
        kind="REPO_SOURCE_CODE",
        canonical_uri="https://github.com/example/model_b",
        title="Repo B 3D Body Mesh",
    )

    # 1. Unregistered frames -> MUST prohibit millimeter subtraction and record UNREGISTERED
    cmp_unregistered = compare_sources(
        comparison_id="cmp_geo_unreg",
        source_a_id="src:mesh:repo_a",
        source_b_id="src:mesh:repo_b",
        classification="NOT_COMPARABLE",
        operator_notes="Different coordinate systems; landmark registration absent.",
        is_geometric=True,
        is_frame_registered=False,
    )
    assert cmp_unregistered["geometric_comparability_state"] == "UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL"
    assert cmp_unregistered["classification"] == "NOT_COMPARABLE"

    # 2. Registered frames -> Validated common frame
    cmp_registered = compare_sources(
        comparison_id="cmp_geo_reg",
        source_a_id="src:mesh:repo_a",
        source_b_id="src:mesh:repo_b",
        classification="DIFFERENCE",
        operator_notes="Aligned via 5 landmark ICP registration.",
        is_geometric=True,
        is_frame_registered=True,
    )
    assert cmp_registered["geometric_comparability_state"] == "REGISTERED_COMMON_FRAME"
