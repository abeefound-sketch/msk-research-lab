"""Typed Knowledge Graph Engine (G9 / R3-06).

Implements strictly-typed SQLite graph nodes and edges, bounded 1-hop
neighborhood retrieval, provenance verification for all edges, and review filtering.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from msk_research_lab.core.db import get_db

ALLOWLISTED_NODE_TYPES = {
    "ANATOMICAL_STRUCTURE",
    "JOINT",
    "MUSCLE",
    "ACUPOINT",
    "MERIDIAN",
    "DIEN_CHAN_POINT",
    "THAI_SEN_LINE",
    "SYMPTOM_TERM",
    "TECHNIQUE",
    "SOURCE",
    "CLAIM",
    "EVIDENCE",
    "CONTRADICTION",
    "REPOSITORY_VERSION",
    "ONTOLOGY_CONCEPT",
}

ALLOWLISTED_EDGE_TYPES = {
    "CITES",
    "SUPPORTS",
    "CONTRADICTS",
    "DERIVED_FROM",
    "TRANSLATION_OF",
    "ALIAS_OF",
    "PART_OF",
    "CONCEPTUALLY_ASSOCIATED_WITH",
    "LOCATED_ON_REFERENCE_MESH",
    "REPORTED_IN_SOURCE",
    "COMPARES_WITH",
    "SUPERSEDES",
}


class GraphError(Exception):
    """Base exception for graph operations."""
    pass


def add_node(
    *,
    node_id: str,
    node_type: str,
    namespace: str,
    label: str,
    stable_ref: Optional[str] = None,
    review_state: str = "UNREVIEWED",
    source_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert or update a typed graph node."""
    if node_type not in ALLOWLISTED_NODE_TYPES:
        raise GraphError(f"Invalid node type '{node_type}'. Allowed: {sorted(ALLOWLISTED_NODE_TYPES)}")

    prop_json = json.dumps(properties or {})
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO graph_nodes (
                node_id, node_type, namespace, label, stable_ref,
                review_state, source_id, properties_json, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '1.0')
            ON CONFLICT(node_id) DO UPDATE SET
                node_type=excluded.node_type,
                namespace=excluded.namespace,
                label=excluded.label,
                stable_ref=excluded.stable_ref,
                review_state=excluded.review_state,
                source_id=excluded.source_id,
                properties_json=excluded.properties_json;
            """,
            (node_id, node_type, namespace, label, stable_ref, review_state, source_id, prop_json)
        )
    return get_node(node_id)


def get_node(node_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve node details by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM graph_nodes WHERE node_id = ?;", (node_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["properties"] = json.loads(res.get("properties_json") or "{}")
        return res


def add_edge(
    *,
    edge_id: str,
    source_node_id: str,
    target_node_id: str,
    relation_type: str,
    provenance_evidence_id: Optional[str] = None,
    assertion_kind: str = "EDUCATIONAL_PROPOSITION",
    review_state: str = "UNREVIEWED",
    confidence_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a directed, typed edge with mandatory provenance for asserted relationships."""
    if relation_type not in ALLOWLISTED_EDGE_TYPES:
        raise GraphError(f"Invalid relation type '{relation_type}'. Allowed: {sorted(ALLOWLISTED_EDGE_TYPES)}")

    src_node = get_node(source_node_id)
    tgt_node = get_node(target_node_id)
    if not src_node:
        raise GraphError(f"Source node '{source_node_id}' does not exist.")
    if not tgt_node:
        raise GraphError(f"Target node '{target_node_id}' does not exist.")

    # Guard: Asserted clinical / associative edges require provenance
    if relation_type in {"CONCEPTUALLY_ASSOCIATED_WITH", "LOCATED_ON_REFERENCE_MESH"} and not provenance_evidence_id:
        raise GraphError(
            f"Provenance required: Edge '{relation_type}' between '{source_node_id}' and '{target_node_id}' must link to a valid provenance_evidence_id."
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO graph_edges (
                edge_id, source_node_id, target_node_id, relation_type,
                assertion_kind, provenance_evidence_id, review_state,
                confidence_text, valid_from
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(edge_id) DO UPDATE SET
                relation_type=excluded.relation_type,
                assertion_kind=excluded.assertion_kind,
                provenance_evidence_id=excluded.provenance_evidence_id,
                review_state=excluded.review_state,
                confidence_text=excluded.confidence_text;
            """,
            (
                edge_id, source_node_id, target_node_id, relation_type,
                assertion_kind, provenance_evidence_id, review_state,
                confidence_text, now_iso
            )
        )
    return get_edge(edge_id)


def get_edge(edge_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve edge details by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM graph_edges WHERE edge_id = ?;", (edge_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_neighborhood(
    node_id: str,
    depth: int = 1,
    include_unreviewed: bool = False,
    limit: int = 50,
) -> Dict[str, Any]:
    """Retrieve bounded 1-hop neighborhood for a graph node."""
    center = get_node(node_id)
    if not center:
        raise GraphError(f"Node '{node_id}' not found.")

    with get_db() as conn:
        review_filter = "" if include_unreviewed else "AND e.review_state IN ('CONTENT_REVIEWED', 'DOMAIN_REVIEWED')"
        query = f"""
            SELECT e.*,
                   s.label as source_label, s.node_type as source_type,
                   t.label as target_label, t.node_type as target_type
            FROM graph_edges e
            JOIN graph_nodes s ON e.source_node_id = s.node_id
            JOIN graph_nodes t ON e.target_node_id = t.node_id
            WHERE (e.source_node_id = ? OR e.target_node_id = ?)
            {review_filter}
            LIMIT ?;
        """
        cur = conn.execute(query, (node_id, node_id, limit))
        edges = [dict(r) for r in cur.fetchall()]

        connected_node_ids = set()
        for e in edges:
            connected_node_ids.add(e["source_node_id"])
            connected_node_ids.add(e["target_node_id"])

        nodes = []
        for n_id in connected_node_ids:
            node = get_node(n_id)
            if node:
                nodes.append(node)

    return {
        "center_node": center,
        "depth": depth,
        "include_unreviewed": include_unreviewed,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "disclaimer": "Graph connections represent documented educational citations; no clinical equivalence inferred.",
    }
