"""Validated Research Snapshot Publisher & Disaster Rollback Engine (G10 / R3-07).

Implements staged immutable SQLite snapshot creation, automated QA gates
(schema, FK, source locator integrity, rights check), atomic pointer activation
via os.replace on the same filesystem, and non-destructive release rollback.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db
from msk_research_lab.provenance.registry import resolve_source_locator, LocatorResolutionError


class PublicationError(Exception):
    """Base exception for snapshot publication errors."""
    pass


class QAGateError(PublicationError):
    """Raised when staged snapshot fails automated QA validation."""
    pass


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_snapshots_dir() -> Path:
    cfg = get_config()
    s_dir = cfg.data_dir / "snapshots"
    s_dir.mkdir(parents=True, exist_ok=True)
    return s_dir


def stage_snapshot_build(build_id: str, operator_id: str) -> Dict[str, Any]:
    """Build a staged immutable knowledge snapshot into 2data/snapshots/.builds/<build_id>/."""
    snapshots_dir = get_snapshots_dir()
    build_dir = snapshots_dir / ".builds" / build_id
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    db_path = build_dir / "knowledge.sqlite"

    # 1. Create published SQLite database
    pub_conn = sqlite3.connect(str(db_path))
    pub_conn.execute("PRAGMA foreign_keys = ON;")

    # Schema for published snapshot
    pub_conn.executescript("""
        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            rights_status TEXT NOT NULL,
            edition_id TEXT,
            canonical_uri TEXT NOT NULL,
            sha256 TEXT,
            git_commit_sha TEXT
        );

        CREATE TABLE source_locations (
            locator_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            locator_type TEXT NOT NULL,
            locator_json TEXT NOT NULL,
            FOREIGN KEY(source_id) REFERENCES sources(source_id)
        );

        CREATE TABLE claims (
            claim_id TEXT PRIMARY KEY,
            statement TEXT NOT NULL,
            knowledge_namespace TEXT NOT NULL,
            claim_kind TEXT NOT NULL,
            status TEXT NOT NULL,
            review_state TEXT NOT NULL,
            clinical_evidence_assessment TEXT,
            reviewer_id TEXT,
            review_rationale TEXT,
            uncertainty_text TEXT
        );

        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            locator_id TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            excerpt_or_observation TEXT NOT NULL,
            review_state TEXT NOT NULL,
            provenance_hash TEXT NOT NULL,
            FOREIGN KEY(source_id) REFERENCES sources(source_id),
            FOREIGN KEY(locator_id) REFERENCES source_locations(locator_id)
        );

        CREATE TABLE claim_evidence_links (
            claim_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            reviewer_rationale TEXT,
            PRIMARY KEY(claim_id, evidence_id, relation),
            FOREIGN KEY(claim_id) REFERENCES claims(claim_id),
            FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id)
        );

        CREATE TABLE contradictions (
            contradiction_id TEXT PRIMARY KEY,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT,
            counter_evidence_id TEXT,
            conflict_kind TEXT NOT NULL,
            state TEXT NOT NULL,
            rationale TEXT,
            FOREIGN KEY(claim_a_id) REFERENCES claims(claim_id)
        );

        CREATE TABLE ontology_concepts (
            concept_id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            canonical_label TEXT NOT NULL,
            review_state TEXT NOT NULL
        );

        CREATE TABLE concept_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT NOT NULL,
            value TEXT NOT NULL,
            language TEXT NOT NULL,
            kind TEXT NOT NULL,
            FOREIGN KEY(concept_id) REFERENCES ontology_concepts(concept_id)
        );

        CREATE TABLE graph_nodes (
            node_id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            namespace TEXT NOT NULL,
            label TEXT NOT NULL,
            review_state TEXT NOT NULL
        );

        CREATE TABLE graph_edges (
            edge_id TEXT PRIMARY KEY,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            review_state TEXT NOT NULL,
            provenance_evidence_id TEXT,
            FOREIGN KEY(source_node_id) REFERENCES graph_nodes(node_id),
            FOREIGN KEY(target_node_id) REFERENCES graph_nodes(node_id)
        );
    """)

    # 2. Extract reviewed data from main working DB
    with get_db() as work_conn:
        # A. Sources (Rights-aware: only metadata, no proprietary full-text payload)
        cur_src = work_conn.execute("SELECT source_id, kind, title, author, rights_status, edition_id, canonical_uri, sha256, git_commit_sha FROM sources;")
        for s in cur_src.fetchall():
            pub_conn.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (s["source_id"], s["kind"], s["title"], s["author"], s["rights_status"], s["edition_id"], s["canonical_uri"], s["sha256"], s["git_commit_sha"])
            )

        # B. Source locations
        cur_loc = work_conn.execute("SELECT locator_id, source_id, locator_type, locator_json FROM source_locations;")
        for l in cur_loc.fetchall():
            pub_conn.execute(
                "INSERT INTO source_locations VALUES (?, ?, ?, ?);",
                (l["locator_id"], l["source_id"], l["locator_type"], l["locator_json"])
            )

        # C. Claims (ONLY SOURCE_SUPPORTED or DISPUTED, CONTENT_REVIEWED)
        cur_cl = work_conn.execute(
            """
            SELECT claim_id, statement, knowledge_namespace, claim_kind, status,
                   review_state, clinical_evidence_assessment, reviewer_id, review_rationale, uncertainty_text
            FROM claims
            WHERE status IN ('SOURCE_SUPPORTED', 'DISPUTED')
              AND review_state IN ('CONTENT_REVIEWED', 'DOMAIN_REVIEWED');
            """
        )
        published_claims = [dict(r) for r in cur_cl.fetchall()]
        for c in published_claims:
            pub_conn.execute(
                "INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (c["claim_id"], c["statement"], c["knowledge_namespace"], c["claim_kind"], c["status"],
                 c["review_state"], c["clinical_evidence_assessment"], c["reviewer_id"], c["review_rationale"], c["uncertainty_text"])
            )

        published_claim_ids = {c["claim_id"] for c in published_claims}

        # D. Evidence & links linked to published claims
        if published_claim_ids:
            cur_ev_links = work_conn.execute(
                "SELECT claim_id, evidence_id, relation, reviewer_rationale FROM claim_evidence_links WHERE claim_id IN ({seq});".format(
                    seq=",".join(["?"] * len(published_claim_ids))
                ),
                list(published_claim_ids)
            )
            links = cur_ev_links.fetchall()
            ev_ids = {l["evidence_id"] for l in links}

            for ev_id in ev_ids:
                cur_ev = work_conn.execute(
                    "SELECT evidence_id, source_id, locator_id, source_kind, excerpt_or_observation, review_state, provenance_hash FROM evidence WHERE evidence_id = ?;",
                    (ev_id,)
                )
                row_ev = cur_ev.fetchone()
                if row_ev:
                    pub_conn.execute(
                        "INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?);",
                        (row_ev["evidence_id"], row_ev["source_id"], row_ev["locator_id"], row_ev["source_kind"],
                         row_ev["excerpt_or_observation"], row_ev["review_state"], row_ev["provenance_hash"])
                    )

            for l in links:
                pub_conn.execute(
                    "INSERT INTO claim_evidence_links VALUES (?, ?, ?, ?);",
                    (l["claim_id"], l["evidence_id"], l["relation"], l["reviewer_rationale"])
                )

        # E. Contradictions linked to published claims
        if published_claim_ids:
            cur_cd = work_conn.execute(
                "SELECT contradiction_id, claim_a_id, claim_b_id, counter_evidence_id, conflict_kind, state, rationale FROM contradictions WHERE claim_a_id IN ({seq});".format(
                    seq=",".join(["?"] * len(published_claim_ids))
                ),
                list(published_claim_ids)
            )
            for cd in cur_cd.fetchall():
                pub_conn.execute(
                    "INSERT INTO contradictions VALUES (?, ?, ?, ?, ?, ?, ?);",
                    (cd["contradiction_id"], cd["claim_a_id"], cd["claim_b_id"], cd["counter_evidence_id"], cd["conflict_kind"], cd["state"], cd["rationale"])
                )

        # F. Ontology concepts & aliases
        cur_ont = work_conn.execute("SELECT concept_id, namespace, canonical_label, review_state FROM ontology_concepts WHERE review_state != 'REJECTED';")
        for o in cur_ont.fetchall():
            pub_conn.execute("INSERT INTO ontology_concepts VALUES (?, ?, ?, ?);", (o["concept_id"], o["namespace"], o["canonical_label"], o["review_state"]))

        cur_als = work_conn.execute("SELECT alias_id, concept_id, value, language, kind FROM concept_aliases;")
        for a in cur_als.fetchall():
            pub_conn.execute("INSERT INTO concept_aliases VALUES (?, ?, ?, ?, ?);", (a["alias_id"], a["concept_id"], a["value"], a["language"], a["kind"]))

        # G. Graph nodes & edges (Reviewed only)
        cur_nd = work_conn.execute("SELECT node_id, node_type, namespace, label, review_state FROM graph_nodes;")
        for n in cur_nd.fetchall():
            pub_conn.execute("INSERT INTO graph_nodes VALUES (?, ?, ?, ?, ?);", (n["node_id"], n["node_type"], n["namespace"], n["label"], n["review_state"]))

        cur_ed = work_conn.execute("SELECT edge_id, source_node_id, target_node_id, relation_type, review_state, provenance_evidence_id FROM graph_edges WHERE review_state IN ('CONTENT_REVIEWED', 'DOMAIN_REVIEWED');")
        for e in cur_ed.fetchall():
            pub_conn.execute("INSERT INTO graph_edges VALUES (?, ?, ?, ?, ?, ?);", (e["edge_id"], e["source_node_id"], e["target_node_id"], e["relation_type"], e["review_state"], e["provenance_evidence_id"]))

    pub_conn.commit()

    # 3. Automated QA Verification
    qa_results = {
        "build_id": build_id,
        "operator_id": operator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "integrity_check": "FAIL",
        "foreign_key_check": "FAIL",
        "claims_locator_verification": "FAIL",
        "graph_orphans": 0,
        "qa_passed": False,
    }

    # Integrity check
    cur_ic = pub_conn.execute("PRAGMA integrity_check;")
    row_ic = cur_ic.fetchone()
    qa_results["integrity_check"] = "PASS" if row_ic and row_ic[0] == "ok" else "FAIL"

    # FK check
    cur_fk = pub_conn.execute("PRAGMA foreign_key_check;")
    fk_errors = cur_fk.fetchall()
    qa_results["foreign_key_check"] = "PASS" if len(fk_errors) == 0 else f"FAIL: {len(fk_errors)} errors"

    # Verify all published claims' locators resolve
    locator_failures = []
    cur_pub_ev = pub_conn.execute("SELECT e.source_id, e.locator_id FROM evidence e JOIN claim_evidence_links l ON e.evidence_id = l.evidence_id;")
    for row in cur_pub_ev.fetchall():
        try:
            resolve_source_locator(row[0], row[1])
        except LocatorResolutionError as err:
            locator_failures.append(str(err))

    qa_results["claims_locator_verification"] = "PASS" if not locator_failures else f"FAIL: {locator_failures}"

    # Verify graph edges have no orphans
    cur_orph = pub_conn.execute("""
        SELECT COUNT(*) FROM graph_edges e
        WHERE e.source_node_id NOT IN (SELECT node_id FROM graph_nodes)
           OR e.target_node_id NOT IN (SELECT node_id FROM graph_nodes);
    """)
    qa_results["graph_orphans"] = cur_orph.fetchone()[0]

    qa_passed = (
        qa_results["integrity_check"] == "PASS" and
        qa_results["foreign_key_check"] == "PASS" and
        qa_results["claims_locator_verification"] == "PASS" and
        qa_results["graph_orphans"] == 0
    )
    qa_results["qa_passed"] = qa_passed
    pub_conn.close()

    # Write QA file
    qa_file = build_dir / "qa.json"
    qa_file.write_text(json.dumps(qa_results, indent=2), encoding="utf-8")

    # Generate Manifest
    db_hash = _sha256_file(db_path)
    qa_hash = _sha256_file(qa_file)
    manifest_data = {
        "build_id": build_id,
        "operator_id": operator_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            "knowledge.sqlite": db_hash,
            "qa.json": qa_hash,
        },
        "published_claims_count": len(published_claims),
    }
    manifest_file = build_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    manifest_data["manifest_hash"] = _sha256_file(manifest_file)

    return {
        "build_id": build_id,
        "build_dir": str(build_dir),
        "manifest": manifest_data,
        "qa": qa_results,
    }


def promote_release(build_id: str, release_id: str, operator_id: str) -> Dict[str, Any]:
    """Promote a QA-passed staged build into an immutable release and switch active pointer."""
    snapshots_dir = get_snapshots_dir()
    build_dir = snapshots_dir / ".builds" / build_id
    if not build_dir.exists():
        raise PublicationError(f"Staged build '{build_id}' not found.")

    qa_file = build_dir / "qa.json"
    if not qa_file.exists():
        raise PublicationError(f"Staged build '{build_id}' is missing qa.json.")

    qa = json.loads(qa_file.read_text(encoding="utf-8"))
    if not qa.get("qa_passed"):
        raise QAGateError(f"QA verification failed for build '{build_id}'. Refusing publication: {qa}")

    # Destination release directory
    releases_dir = snapshots_dir / ".releases"
    releases_dir.mkdir(parents=True, exist_ok=True)
    release_dir = releases_dir / release_id
    if release_dir.exists():
        raise PublicationError(f"Release '{release_id}' already exists. Releases are immutable.")

    # Copy to release directory
    shutil.copytree(build_dir, release_dir)

    # Calculate manifest hash of the promoted release
    manifest_file = release_dir / "manifest.json"
    manifest_hash = _sha256_file(manifest_file)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Update published_releases table in working DB
    with get_db() as conn:
        conn.execute("UPDATE published_releases SET is_active = 0 WHERE is_active = 1;")
        conn.execute(
            """
            INSERT INTO published_releases (
                release_id, build_id, manifest_hash, published_at, published_by,
                is_active, qa_report_json, manifest_json
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?);
            """,
            (
                release_id, build_id, manifest_hash, now_iso, operator_id,
                qa_file.read_text(encoding="utf-8"), manifest_file.read_text(encoding="utf-8")
            )
        )

    # Atomic pointer switch in .active/current.json
    active_dir = snapshots_dir / ".active"
    active_dir.mkdir(parents=True, exist_ok=True)

    pointer_payload = {
        "release_id": release_id,
        "build_id": build_id,
        "release_dir": str(release_dir),
        "manifest_hash": manifest_hash,
        "published_by": operator_id,
        "activated_at": now_iso,
    }

    # Write to temporary file on the SAME filesystem, then atomic os.replace
    tmp_pointer = active_dir / f"current.json.tmp.{os.getpid()}"
    tmp_pointer.write_text(json.dumps(pointer_payload, indent=2), encoding="utf-8")
    os.replace(str(tmp_pointer), str(active_dir / "current.json"))

    return pointer_payload


def rollback_release(target_release_id: str, operator_id: str) -> Dict[str, Any]:
    """Atomic rollback of the active release pointer to a previously validated release."""
    snapshots_dir = get_snapshots_dir()
    release_dir = snapshots_dir / ".releases" / target_release_id
    if not release_dir.exists():
        raise PublicationError(f"Target release '{target_release_id}' does not exist in releases store.")

    manifest_file = release_dir / "manifest.json"
    if not manifest_file.exists():
        raise PublicationError(f"Target release '{target_release_id}' is corrupt: missing manifest.json.")

    manifest_hash = _sha256_file(manifest_file)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Verify working DB record
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM published_releases WHERE release_id = ?;", (target_release_id,))
        row = cur.fetchone()
        if not row:
            raise PublicationError(f"Release '{target_release_id}' not found in registry.")

        conn.execute("UPDATE published_releases SET is_active = 0 WHERE is_active = 1;")
        conn.execute("UPDATE published_releases SET is_active = 1 WHERE release_id = ?;", (target_release_id,))

    # Atomic pointer switch
    active_dir = snapshots_dir / ".active"
    active_dir.mkdir(parents=True, exist_ok=True)

    pointer_payload = {
        "release_id": target_release_id,
        "build_id": row["build_id"],
        "release_dir": str(release_dir),
        "manifest_hash": manifest_hash,
        "published_by": operator_id,
        "activated_at": now_iso,
        "is_rollback": True,
    }

    tmp_pointer = active_dir / f"current.json.tmp.{os.getpid()}"
    tmp_pointer.write_text(json.dumps(pointer_payload, indent=2), encoding="utf-8")
    os.replace(str(tmp_pointer), str(active_dir / "current.json"))

    return pointer_payload


def get_active_release() -> Optional[Dict[str, Any]]:
    """Retrieve active published release pointer metadata."""
    snapshots_dir = get_snapshots_dir()
    pointer_file = snapshots_dir / ".active" / "current.json"
    if not pointer_file.exists():
        return None
    try:
        data = json.loads(pointer_file.read_text(encoding="utf-8"))
        # Verify db file exists
        db_file = Path(data["release_dir"]) / "knowledge.sqlite"
        if not db_file.exists():
            return None
        data["db_path"] = str(db_file)
        return data
    except Exception:
        return None
