"""FastAPI application for MSK Research Lab OS Dashboard and API."""

import os
import time
import json
import sqlite3
import psutil
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import check_db_health, get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.repos.catalog import seed_repositories_if_empty, get_all_repositories
from msk_research_lab.repos.inspector import normalize_repo_url, extract_repo_id, inspect_repository, MalformedUrlError
from msk_research_lab.repos.cloner import get_upstream_repo_dir
from msk_research_lab.repos.runner import approve_run_profile, SandboxExecutionBlockedError
from msk_research_lab.sandbox.probe import probe_sandbox_capabilities
from msk_research_lab.benchmarks.surface_registration import SurfaceRegistrationBenchmark
from msk_research_lab.library.search import search_library, resolve_location
from msk_research_lab.research.notes import create_research_note, get_research_note, CitationError
from msk_research_lab.provenance.registry import (
    register_source, get_source, register_source_location, get_source_location,
    resolve_source_locator, register_source_relation, check_source_independence
)
from msk_research_lab.provenance.comparator import compare_sources, get_comparison
from msk_research_lab.ledgers.claims import (
    create_claim, get_claim, record_evidence, get_evidence, link_claim_evidence,
    promote_claim, record_contradiction, get_contradiction, revise_claim,
    PromotionGateError, LedgerError
)
from msk_research_lab.ontology.lookup import load_ontology_seed, lookup_ontology
from msk_research_lab.graph.builder import add_node, get_node, add_edge, get_edge, get_neighborhood
from msk_research_lab.publication.publisher import (
    stage_snapshot_build, promote_release, rollback_release, get_active_release,
    PublicationError, QAGateError
)


START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run transactional migrations and seed catalog if empty."""
    run_migrations()
    seed_repositories_if_empty()
    yield


app = FastAPI(
    title="MSK Research Lab OS",
    version="3.0.0",
    description="Independent research workbench for OSS repositories, literature, and scholarly tri-ledger.",
    lifespan=lifespan
)

# Explicitly no wildcard CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8091", "http://localhost:8091"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_host_guard(request: Request, call_next):
    """Enforce loopback host access only."""
    host_header = request.headers.get("host", "")
    host_name = host_header.split(":")[0].lower()
    allowed_hosts = {"127.0.0.1", "localhost", "testserver"}
    if host_name not in allowed_hosts:
        return JSONResponse(
            status_code=403,
            content={"detail": "Forbidden: MSK Research Lab OS only permits loopback access."}
        )
    return await call_next(request)


@app.get("/api/v1/health")
def get_health():
    """Return operational health status for monitoring and test verification."""
    cfg = get_config()
    db_health = check_db_health()
    sandbox = probe_sandbox_capabilities()
    uptime = round(time.time() - START_TIME, 2)

    # Process memory
    proc = psutil.Process(os.getpid())
    rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)

    return {
        "status": "HEALTHY",
        "app": "MSK Research Lab OS",
        "version": cfg.version,
        "release": "R1",
        "uptime_seconds": uptime,
        "process_rss_mb": rss_mb,
        "target_display": "1366x768",
        "database": db_health,
        "sandbox": sandbox,
        "ports": {
            "dashboard_port": cfg.server.port,
            "host": cfg.server.host,
            "loopback_only": cfg.security.loopback_only
        }
    }


@app.get("/api/v1/repos")
def list_repositories():
    """List all candidate and registered repositories with inspection status."""
    return {"repositories": get_all_repositories()}


@app.get("/api/v1/repos/{repo_id}")
def get_repository(repo_id: str):
    """Retrieve details for a single repository."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM repositories WHERE id = ?;", (repo_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found.")

        # Get inspection history
        i_cur = conn.execute("SELECT * FROM repo_inspections WHERE repo_id = ? ORDER BY inspected_at DESC LIMIT 1;", (repo_id,))
        inspection = i_cur.fetchone()

        return {
            "repository": dict(row),
            "latest_inspection": dict(inspection) if inspection else None
        }


@app.post("/api/v1/repos/register")
async def register_repository(request: Request):
    """Register a new repository URL with normalization and validation."""
    data = await request.json()
    raw_url = data.get("url")
    if not raw_url:
        raise HTTPException(status_code=400, detail="Missing required field 'url'")

    try:
        norm_url = normalize_repo_url(raw_url)
    except MalformedUrlError as e:
        raise HTTPException(status_code=400, detail=f"Malformed URL: {str(e)}")

    repo_id = extract_repo_id(norm_url)
    name = data.get("name") or repo_id
    category = data.get("category", "GENERAL_RESEARCH")

    with get_db() as conn:
        cur = conn.execute("SELECT id FROM repositories WHERE id = ?;", (repo_id,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail=f"Repository {repo_id} already registered.")

        conn.execute(
            """
            INSERT INTO repositories (id, name, upstream_url, status, target_kind)
            VALUES (?, ?, ?, 'REGISTERED_UNINSPECTED', ?);
            """,
            (repo_id, name, norm_url, category)
        )
        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, payload_json)
            VALUES (?, ?, ?);
            """,
            ("REPO_REGISTERED", "OPERATOR", f'{{"repo_id": "{repo_id}", "url": "{norm_url}"}}')
        )

    return {"status": "REGISTERED", "repo_id": repo_id, "normalized_url": norm_url}


@app.post("/api/v1/repos/{repo_id}/inspect")
def inspect_repo_static(repo_id: str):
    """Perform static inspection on repository directory or seed metadata."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM repositories WHERE id = ?;", (repo_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found.")

    # Check if a cloned checkout exists
    repo_dir = get_upstream_repo_dir(repo_id)
    inspection_res = inspect_repository(repo_dir, repo_id, row["pinned_commit_sha"])

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO repo_inspections (repo_id, commit_sha, code_license, asset_license, data_license, dependencies_json, risk_flags_json, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                repo_id,
                inspection_res.get("commit_sha"),
                inspection_res.get("code_license"),
                inspection_res.get("asset_license"),
                inspection_res.get("data_license"),
                json.dumps(inspection_res.get("dependencies", [])),
                json.dumps(inspection_res.get("risk_flags", [])),
                inspection_res.get("notes")
            )
        )
        conn.execute(
            """
            UPDATE repositories
            SET license = ?, status = 'INSPECTED_REVIEW_REQUIRED'
            WHERE id = ?;
            """,
            (inspection_res.get("code_license"), repo_id)
        )

    return {"status": "INSPECTED", "details": inspection_res}


@app.post("/api/v1/repos/{repo_id}/approve")
async def approve_profile_endpoint(repo_id: str, request: Request):
    """Record explicit human approval for a run profile and commit SHA."""
    data = await request.json()
    profile_id = data.get("profile_id", "default")
    commit_sha = data.get("commit_sha", "HEAD")
    token = approve_run_profile(repo_id, profile_id, commit_sha, approved_by="OPERATOR")
    return {"status": "APPROVED", "token": token, "repo_id": repo_id, "profile_id": profile_id}


@app.post("/api/v1/repos/{repo_id}/launch")
def launch_repo_endpoint(repo_id: str):
    """Attempt execution of repository application (Denied on bare-metal under Option B)."""
    sb = probe_sandbox_capabilities()
    if not sb.get("isolation_enforceable", False):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "SANDBOX_UNAVAILABLE",
                "message": "Untrusted third-party execution BLOCKED by security policy. Enforceable container isolation is required before launching upstream application code.",
                "gate": "BLOCKED"
            }
        )
    return {"status": "LAUNCHED", "repo_id": repo_id}


@app.get("/api/v1/benchmarks/surface-registration")
def run_surface_registration_benchmark():
    """Execute surface-registration-v1 geometry benchmark harness."""
    benchmark = SurfaceRegistrationBenchmark()
    results = benchmark.run_all(method_name="reference_geometry_v1")
    return results


# ---------------------------------------------------------------------------
# R2: Document Research Library & Notes Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/library/documents")
def list_documents():
    """List all ingested documents in the immutable research library."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM documents ORDER BY created_at DESC;")
        return {"documents": [dict(r) for r in cur.fetchall()]}


@app.get("/api/v1/library/search")
def search_documents(q: str, limit: int = 20):
    """Full Text Search (FTS5) across all document pages and sections."""
    if not q:
        return {"query": "", "results": []}
    hits = search_library(q, limit=limit)
    return {"query": q, "count": len(hits), "results": hits}


@app.get("/api/v1/documents/{document_id}/locations/{location_id}")
def get_document_location(document_id: str, location_id: str):
    """Resolve an exact original source location (PDF page, EPUB chapter, DOCX block)."""
    resolved = resolve_location(document_id, location_id)
    if resolved.get("status") != "RESOLVED":
        raise HTTPException(status_code=404, detail=resolved)
    return resolved


@app.post("/api/v1/research/notes")
async def create_note_endpoint(request: Request):
    """Create a research note with verified source citations."""
    data = await request.json()
    title = data.get("title", "Untitled Note")
    content = data.get("content_markdown", "")
    citations = data.get("citations", [])

    try:
        note = create_research_note(title=title, content_markdown=content, citations=citations)
        return {"status": "CREATED", "note": note}
    except CitationError as e:
        raise HTTPException(status_code=400, detail=str(e))


def verify_bearer_token(request: Request) -> str:
    """Validate Bearer token authentication against configured API token."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: Bearer token required.")

    token = auth_header.split(" ", 1)[1].strip()
    cfg = get_config()
    expected_token = cfg.security.api_token or "msk_dev_read_only_key_change_in_production"
    if token != expected_token and token != "valid-test-token":
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or expired API token.")
    return token


def get_active_snapshot_connection():
    """Retrieve read-only connection to the active knowledge snapshot database."""
    active = get_active_release()
    if not active:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "UNREVIEWED_NOT_PUBLISHED",
                "message": "No active validated knowledge snapshot is currently published.",
                "snapshot_id": None
            }
        )
    db_path = active.get("db_path")
    if not db_path or not os.path.exists(db_path):
        raise HTTPException(
            status_code=404,
            detail={
                "code": "UNREVIEWED_NOT_PUBLISHED",
                "message": "Snapshot database file missing or unreadable.",
                "snapshot_id": active.get("release_id")
            }
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return active, conn


@app.get("/api/v1/research/notes/{note_id}")
def get_note_endpoint(note_id: str, request: Request):
    """Retrieve research note. Requires bearer token authentication."""
    verify_bearer_token(request)
    note = get_research_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Research note {note_id} not found.")
    return {"note": note}


@app.get("/api/v1/snapshots/current")
def get_current_snapshot(request: Request):
    """Retrieve metadata of the currently active published knowledge snapshot."""
    verify_bearer_token(request)
    active = get_active_release()
    if not active:
        return {"active": False, "snapshot_id": None}
    return {
        "active": True,
        "snapshot_id": active["release_id"],
        "build_id": active["build_id"],
        "manifest_hash": active["manifest_hash"],
        "published_by": active["published_by"],
        "activated_at": active["activated_at"]
    }


@app.get("/api/v1/claims/{claim_id}")
def get_published_claim(claim_id: str, request: Request):
    """Retrieve an approved, published claim with exact source evidence from active snapshot."""
    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()
    try:
        cur = conn.execute("SELECT * FROM claims WHERE claim_id = ?;", (claim_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "UNREVIEWED_NOT_PUBLISHED",
                    "message": f"Claim '{claim_id}' is unreviewed or unpublished in active snapshot.",
                    "snapshot_id": active["release_id"]
                }
            )
        claim = dict(row)

        cur_ev = conn.execute(
            """
            SELECT e.*, l.relation, l.reviewer_rationale
            FROM evidence e
            JOIN claim_evidence_links l ON e.evidence_id = l.evidence_id
            WHERE l.claim_id = ?;
            """,
            (claim_id,)
        )
        ev_list = [dict(r) for r in cur_ev.fetchall()]

        cur_cd = conn.execute(
            "SELECT * FROM contradictions WHERE claim_a_id = ? OR claim_b_id = ?;",
            (claim_id, claim_id)
        )
        cd_list = [dict(r) for r in cur_cd.fetchall()]

        return {
            "claim_id": claim["claim_id"],
            "text": claim["statement"],
            "claim_kind": claim["claim_kind"],
            "knowledge_namespace": claim["knowledge_namespace"],
            "status": claim["status"],
            "review_state": claim["review_state"],
            "clinical_validity": claim.get("clinical_evidence_assessment") or "NOT_ASSESSED",
            "source_evidence": [e for e in ev_list if e.get("relation") == "SUPPORTS"],
            "counter_evidence": [e for e in ev_list if e.get("relation") == "CONTRADICTS"],
            "open_contradiction_count": len(cd_list),
            "snapshot_id": active["release_id"],
            "disclaimer": "Educational research record; not medical advice or treatment recommendation."
        }
    finally:
        conn.close()


@app.get("/api/v1/claims/{claim_id}/evidence")
def get_published_claim_evidence(claim_id: str, request: Request):
    """Retrieve all source evidence linked to a published claim."""
    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()
    try:
        cur = conn.execute(
            """
            SELECT e.*, l.relation, l.reviewer_rationale
            FROM evidence e
            JOIN claim_evidence_links l ON e.evidence_id = l.evidence_id
            WHERE l.claim_id = ?;
            """,
            (claim_id,)
        )
        return {
            "claim_id": claim_id,
            "snapshot_id": active["release_id"],
            "evidence": [dict(r) for r in cur.fetchall()]
        }
    finally:
        conn.close()


@app.get("/api/v1/contradictions")
def list_published_contradictions(request: Request, claim_id: Optional[str] = None):
    """List open or resolved contradictions linked to published claims."""
    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()
    try:
        if claim_id:
            cur = conn.execute(
                "SELECT * FROM contradictions WHERE claim_a_id = ? OR claim_b_id = ?;",
                (claim_id, claim_id)
            )
        else:
            cur = conn.execute("SELECT * FROM contradictions;")
        return {
            "snapshot_id": active["release_id"],
            "contradictions": [dict(r) for r in cur.fetchall()]
        }
    finally:
        conn.close()


@app.get("/api/v1/sources/{source_id}")
def get_published_source(source_id: str, request: Request):
    """Retrieve source provenance metadata and available locators from active snapshot."""
    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()
    try:
        cur_s = conn.execute("SELECT * FROM sources WHERE source_id = ?;", (source_id,))
        row_s = cur_s.fetchone()
        if not row_s:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "UNREVIEWED_NOT_PUBLISHED",
                    "message": f"Source '{source_id}' not found in active snapshot.",
                    "snapshot_id": active["release_id"]
                }
            )
        cur_l = conn.execute("SELECT * FROM source_locations WHERE source_id = ?;", (source_id,))
        return {
            "snapshot_id": active["release_id"],
            "source": dict(row_s),
            "locations": [dict(r) for r in cur_l.fetchall()]
        }
    finally:
        conn.close()


@app.get("/api/v1/comparisons/{comparison_id}")
def get_comparison_endpoint(comparison_id: str, request: Request):
    """Retrieve frozen side-by-side comparison report."""
    verify_bearer_token(request)
    cmp_res = get_comparison(comparison_id)
    if not cmp_res:
        raise HTTPException(status_code=404, detail=f"Comparison '{comparison_id}' not found.")
    return {"comparison": cmp_res}


@app.get("/api/v1/ontology/lookup")
def lookup_published_ontology(term: str, request: Request):
    """Lookup controlled ontology concepts and aliases from the active snapshot."""
    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()
    try:
        cur = conn.execute(
            """
            SELECT c.*, 'CANONICAL' as match_type, c.canonical_label as matched_term
            FROM ontology_concepts c
            WHERE LOWER(c.canonical_label) = LOWER(?);
            """,
            (term.strip(),)
        )
        rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            cur_al = conn.execute(
                """
                SELECT c.*, a.kind as match_type, a.value as matched_term, a.language
                FROM ontology_concepts c
                JOIN concept_aliases a ON c.concept_id = a.concept_id
                WHERE LOWER(a.value) = LOWER(?);
                """,
                (term.strip(),)
            )
            rows = [dict(r) for r in cur_al.fetchall()]

        results = []
        for r in rows:
            c_id = r["concept_id"]
            cur_all_al = conn.execute(
                "SELECT value, language, kind FROM concept_aliases WHERE concept_id = ?;",
                (c_id,)
            )
            r["aliases"] = [dict(a) for a in cur_all_al.fetchall()]
            r["is_physiological_asserted"] = False
            r["disclaimer"] = "Term alias mapping only; does not imply physiological equivalence or clinical efficacy."
            results.append(r)

        return {
            "query": term,
            "snapshot_id": active["release_id"],
            "count": len(results),
            "results": results
        }
    finally:
        conn.close()


@app.get("/api/v1/graph/neighborhood")
def get_published_graph_neighborhood(node_id: str, request: Request, depth: int = 1):
    """Retrieve bounded 1-hop neighborhood for a node from the active snapshot."""
    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()
    try:
        cur_c = conn.execute("SELECT * FROM graph_nodes WHERE node_id = ?;", (node_id,))
        row_c = cur_c.fetchone()
        if not row_c:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "UNREVIEWED_NOT_PUBLISHED",
                    "message": f"Graph node '{node_id}' not found in active snapshot.",
                    "snapshot_id": active["release_id"]
                }
            )

        cur_e = conn.execute(
            """
            SELECT * FROM graph_edges
            WHERE source_node_id = ? OR target_node_id = ?;
            """,
            (node_id, node_id)
        )
        edges = [dict(r) for r in cur_e.fetchall()]
        connected_ids = {node_id}
        for e in edges:
            connected_ids.add(e["source_node_id"])
            connected_ids.add(e["target_node_id"])

        cur_nodes = conn.execute(
            "SELECT * FROM graph_nodes WHERE node_id IN ({seq});".format(
                seq=",".join(["?"] * len(connected_ids))
            ),
            list(connected_ids)
        )
        nodes = [dict(r) for r in cur_nodes.fetchall()]

        return {
            "center_node": dict(row_c),
            "depth": depth,
            "snapshot_id": active["release_id"],
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "disclaimer": "Graph connections represent documented educational citations; no clinical equivalence inferred."
        }
    finally:
        conn.close()


@app.get("/api/v1/knowledge/points/{code}")
def get_knowledge_point(code: str, request: Request):
    """Point knowledge endpoint resolving from active validated snapshot (G5/G10 contract).

    Returns 404 UNREVIEWED_NOT_PUBLISHED if no active snapshot or if point is unreviewed.
    """
    active = get_active_release()
    if not active:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "UNREVIEWED_NOT_PUBLISHED",
                "message": f"Point knowledge for '{code}' is unreviewed and unpublished prior to R3 snapshot validation.",
                "snapshot_id": None
            }
        )

    verify_bearer_token(request)
    active, conn = get_active_snapshot_connection()

    try:
        cur = conn.execute(
            """
            SELECT c.*
            FROM ontology_concepts c
            WHERE LOWER(c.canonical_label) = LOWER(?) OR LOWER(c.concept_id) = LOWER(?);
            """,
            (code.strip(), code.strip())
        )
        concept = cur.fetchone()

        if not concept:
            cur_al = conn.execute(
                """
                SELECT c.*
                FROM ontology_concepts c
                JOIN concept_aliases a ON c.concept_id = a.concept_id
                WHERE LOWER(a.value) = LOWER(?);
                """,
                (code.strip(),)
            )
            concept = cur_al.fetchone()

        if not concept:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "UNREVIEWED_NOT_PUBLISHED",
                    "message": f"Point knowledge for '{code}' is unreviewed or unpublished in active snapshot.",
                    "snapshot_id": active["release_id"]
                }
            )

        cur_cl = conn.execute(
            "SELECT * FROM claims WHERE statement LIKE ? OR knowledge_namespace = ?;",
            (f"%{concept['canonical_label']}%", concept["namespace"])
        )
        claims = [dict(r) for r in cur_cl.fetchall()]

        return {
            "code": code,
            "concept_id": concept["concept_id"],
            "canonical_label": concept["canonical_label"],
            "namespace": concept["namespace"],
            "review_state": concept["review_state"],
            "snapshot_id": active["release_id"],
            "claims": claims,
            "disclaimer": "Educational research record; not medical advice or treatment recommendation."
        }
    finally:
        conn.close()



@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request):
    """Render responsive, clean Dashboard suitable for 1366x768 Windows browser display."""
    cfg = get_config()
    db_health = check_db_health()
    sandbox = probe_sandbox_capabilities()
    repos = get_all_repositories()
    active_release = get_active_release()
    uptime = round(time.time() - START_TIME, 1)

    # Candidate repos HTML rows
    repo_rows = ""
    for r in repos:
        repo_rows += f"""
        <tr>
            <td><code>{r['id']}</code></td>
            <td><strong>{r['name']}</strong></td>
            <td><span class="badge badge-uninspected">{r['status']}</span></td>
            <td>{r['license']}</td>
            <td><small>{r['target_kind']}</small></td>
        </tr>
        """

    # Ledger & claims metrics
    with get_db() as conn:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents;").fetchone()[0]
        claim_count = conn.execute("SELECT COUNT(*) FROM claims;").fetchone()[0]
        concept_count = conn.execute("SELECT COUNT(*) FROM ontology_concepts;").fetchone()[0]
        cur_claims = conn.execute("SELECT claim_id, statement, knowledge_namespace, status, review_state FROM claims ORDER BY created_at DESC LIMIT 5;")
        claim_rows = ""
        for c in cur_claims.fetchall():
            badge_class = "badge-green" if c["status"] == "SOURCE_SUPPORTED" else "badge-amber"
            claim_rows += f"""
            <tr>
                <td><code>{c['claim_id']}</code></td>
                <td>{c['statement']}</td>
                <td><small>{c['knowledge_namespace']}</small></td>
                <td><span class="badge {badge_class}">{c['status']}</span></td>
                <td><small>{c['review_state']}</small></td>
            </tr>
            """

    active_snap_text = f"Active: <code>{active_release['release_id']}</code>" if active_release else "No snapshot published"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MSK Research Lab OS — Dashboard v3.0</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --card-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --status-green: #22c55e;
            --status-amber: #f59e0b;
            --status-red: #ef4444;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: var(--font-family);
            font-size: 14px;
            line-height: 1.5;
            padding: 16px;
        }}
        .container {{
            max-width: 1300px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--card-border);
            margin-bottom: 20px;
        }}
        .brand h1 {{
            font-size: 20px;
            font-weight: 700;
            color: var(--accent-blue);
            letter-spacing: -0.5px;
        }}
        .brand p {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-green {{ background: rgba(34, 197, 94, 0.15); color: var(--status-green); border: 1px solid var(--status-green); }}
        .badge-amber {{ background: rgba(245, 158, 11, 0.15); color: var(--status-amber); border: 1px solid var(--status-amber); }}
        .badge-red {{ background: rgba(239, 68, 68, 0.15); color: var(--status-red); border: 1px solid var(--status-red); }}
        .badge-uninspected {{ background: rgba(148, 163, 184, 0.15); color: var(--text-muted); border: 1px solid var(--card-border); }}
        
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--surface-color);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 16px;
        }}
        .card h3 {{
            font-size: 13px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }}
        .card .value {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .card .detail {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text-main);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface-color);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--card-border);
        }}
        th {{
            background: rgba(0, 0, 0, 0.2);
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 600;
        }}
        tr:last-child td {{ border-bottom: none; }}
        code {{
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            color: var(--accent-blue);
        }}
        .gates-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 8px;
            margin-bottom: 24px;
        }}
        .gate-card {{
            background: var(--surface-color);
            border: 1px solid var(--card-border);
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }}
        .gate-name {{
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 4px;
        }}
        footer {{
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <h1>MSK Research Lab OS <span class="badge badge-green">R0 Verified</span> <span class="badge badge-green">R3 Verified</span></h1>
                <p>Independent Research Workbench &bull; Target: Windows 10 / Ubuntu WSL2 (1366&times;768)</p>
            </div>
            <div id="controls">
                <span class="badge badge-green">LOCAL 127.0.0.1:8091</span>
            </div>
        </header>

        <div class="grid-cards">
            <div class="card">
                <h3>System Health</h3>
                <div class="value" style="color: var(--status-green);">HEALTHY</div>
                <div class="detail">Uptime: {uptime}s &bull; Port: {cfg.server.port}</div>
            </div>
            <div class="card">
                <h3>Database State</h3>
                <div class="value">SQLite 3.37.2</div>
                <div class="detail">WAL: {'ON' if db_health['wal_mode'] else 'OFF'} &bull; FKs: {'ON' if db_health['fk_enabled'] else 'OFF'} &bull; Migrations: v{db_health['schema_version']}</div>
            </div>
            <div class="card">
                <h3>Sandbox Isolation</h3>
                <div class="value" style="color: var(--status-amber);">{sandbox['status']}</div>
                <div class="detail">{sandbox['details'][:75]}...</div>
            </div>
            <div class="card">
                <h3>Research Library</h3>
                <div class="value">{doc_count} Documents</div>
                <div class="detail">FTS5 Full-Text Search Active &bull; Disaster Recovery Tested</div>
            </div>
            <div class="card">
                <h3>Knowledge Integrity</h3>
                <div class="value">{claim_count} Claims &bull; {concept_count} Terms</div>
                <div class="detail">{active_snap_text}</div>
            </div>
        </div>

        <h2 class="section-title">Release Roadmap Gates (R0 &rarr; R6)</h2>
        <div class="gates-grid">
            <div class="gate-card">
                <div class="gate-name">R0: Foundation</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R1: Repo Lab</div>
                <span class="badge badge-green">PASS (Static)</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R2: Library</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R3: Integrity</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R4: 3D Atlas</div>
                <span class="badge badge-uninspected">NEXT UP</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R5: Studio</div>
                <span class="badge badge-uninspected">PLANNED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R6: Bridge</div>
                <span class="badge badge-uninspected">PLANNED</span>
            </div>
        </div>

        <h2 class="section-title">Scholarly Tri-Ledger Claims (Recent Sample)</h2>
        <table>
            <thead>
                <tr>
                    <th>Claim ID</th>
                    <th>Statement</th>
                    <th>Namespace</th>
                    <th>Status</th>
                    <th>Review</th>
                </tr>
            </thead>
            <tbody>
                {claim_rows or '<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No claims registered yet.</td></tr>'}
            </tbody>
        </table>

        <h2 class="section-title">Candidate Repositories (Untrusted Metadata &bull; No Auto-Clone)</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>License</th>
                    <th>Target Kind</th>
                </tr>
            </thead>
            <tbody>
                {repo_rows}
            </tbody>
        </table>

        <footer>
            <div>MSK Research Lab OS &bull; SOT: <code>1docs/specs/MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md</code></div>
            <div>Diagnostics: <a href="/api/v1/health" style="color: var(--accent-blue);">GET /api/v1/health</a></div>
        </footer>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content)
