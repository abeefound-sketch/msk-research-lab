"""Unit tests for Controlled Multilingual Ontology and Typed Knowledge Graph (G9 / R3-05, R3-06)."""

import pytest
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.ontology.lookup import load_ontology_seed, lookup_ontology
from msk_research_lab.graph.builder import (
    add_node,
    get_node,
    add_edge,
    get_edge,
    get_neighborhood,
    GraphError,
)
from msk_research_lab.provenance.registry import register_source, register_source_location
from msk_research_lab.ledgers.claims import record_evidence


@pytest.fixture(autouse=True)
def setup_ontology_db():
    run_migrations()


def test_ontology_seed_and_multilingual_lookup():
    seed_res = load_ontology_seed()
    assert seed_res["status"] == "SUCCESS"
    assert seed_res["concepts_loaded"] >= 1


    # 1. Lookup by canonical label "GB21"
    hits_gb = lookup_ontology("GB21")
    assert len(hits_gb) == 1
    assert hits_gb[0]["concept_id"] == "tcm:acupoint:GB21"
    assert hits_gb[0]["is_physiological_asserted"] is False
    assert "disclaimer" in hits_gb[0]

    # 2. Lookup by Chinese transliteration "Jianjing"
    hits_jj = lookup_ontology("Jianjing")
    assert len(hits_jj) == 1
    assert hits_jj[0]["concept_id"] == "tcm:acupoint:GB21"

    # 3. Lookup by Vietnamese traditional name "Kiên tỉnh"
    hits_vi = lookup_ontology("Kiên tỉnh")
    assert len(hits_vi) == 1
    assert hits_vi[0]["concept_id"] == "tcm:acupoint:GB21"

    # 4. Lookup by normalized query without diacritics "kien tinh"
    hits_norm = lookup_ontology("kien tinh")
    assert len(hits_norm) == 1
    assert hits_norm[0]["concept_id"] == "tcm:acupoint:GB21"

    # 5. Unknown alias lookup returns empty (does not invent clinical equivalence)
    hits_unknown = lookup_ontology("CompletelyUnknownAcupoint123")
    assert len(hits_unknown) == 0


def test_typed_graph_nodes_and_edges():
    # Setup mock evidence for edge provenance
    register_source(
        source_id="src:anat:gray",
        kind="TEXTBOOK",
        canonical_uri="file:///refs/gray.pdf",
        title="Gray's Anatomy",
    )
    register_source_location(
        locator_id="loc:gray:p100",
        source_id="src:anat:gray",
        locator_type="PDF_PAGE",
        locator_details={"page": 100},
    )
    ev = record_evidence(
        evidence_id="ev:trapezius:cervical",
        source_id="src:anat:gray",
        locator_id="loc:gray:p100",
        source_kind="TEXTBOOK",
        excerpt_or_observation="Trapezius muscle attaches to spinous processes of C7-T12.",
    )

    # 1. Add typed nodes
    node_point = add_node(
        node_id="node:point:GB21",
        node_type="ACUPOINT",
        namespace="TRADITIONAL_ACUPUNCTURE",
        label="GB21 (Jianjing)",
        review_state="CONTENT_REVIEWED",
    )
    node_muscle = add_node(
        node_id="node:muscle:trapezius",
        node_type="MUSCLE",
        namespace="SOMATIC_ANATOMY",
        label="Upper Trapezius Muscle",
        review_state="CONTENT_REVIEWED",
    )
    assert node_point["node_type"] == "ACUPOINT"
    assert node_muscle["node_type"] == "MUSCLE"

    # 2. Add associative edge WITHOUT evidence -> Must fail with GraphError
    with pytest.raises(GraphError, match="Provenance required"):
        add_edge(
            edge_id="edge:gb21_to_trapezius",
            source_node_id="node:point:GB21",
            target_node_id="node:muscle:trapezius",
            relation_type="CONCEPTUALLY_ASSOCIATED_WITH",
            provenance_evidence_id=None,
        )

    # 3. Add associative edge WITH verified evidence -> Succeeds
    edge = add_edge(
        edge_id="edge:gb21_to_trapezius",
        source_node_id="node:point:GB21",
        target_node_id="node:muscle:trapezius",
        relation_type="CONCEPTUALLY_ASSOCIATED_WITH",
        provenance_evidence_id="ev:trapezius:cervical",
        review_state="CONTENT_REVIEWED",
        confidence_text="Topographic correlation described in manual therapy textbook.",
    )
    assert edge["relation_type"] == "CONCEPTUALLY_ASSOCIATED_WITH"
    assert edge["provenance_evidence_id"] == "ev:trapezius:cervical"

    # 4. Bounded 1-hop neighborhood query
    neighborhood = get_neighborhood("node:point:GB21", depth=1)
    assert neighborhood["node_count"] == 2
    assert neighborhood["edge_count"] == 1
    assert neighborhood["edges"][0]["edge_id"] == "edge:gb21_to_trapezius"
    assert "disclaimer" in neighborhood
