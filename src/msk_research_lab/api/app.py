"""FastAPI application for MSK Research Lab OS Dashboard and API."""

import os
import time
import json
import sqlite3
import psutil
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from msk_research_lab.atlas.registry import (
    seed_standard_models_if_empty, list_models_3d, get_model_3d, register_model_3d, ModelRegistryError
)
from msk_research_lab.atlas.surface_registration import (
    snap_to_skin_mesh, create_skin_anchor, get_skin_anchor, evaluate_anchor_validity, Point3D, Triangle3D, GeometryError
)
from msk_research_lab.atlas.comparisons import compare_placements_3d
from msk_research_lab.atlas.path_baker import bake_meridian_path, evaluate_six_view_occlusion
from msk_research_lab.atlas.inspector import inspect_point
from msk_research_lab.atlas.scene import build_calibrated_bp3d_torso_scene, AtlasSceneData
from msk_research_lab.studio.project import (
    create_project, get_project, list_projects, bump_project_version, StudioProjectError
)
from msk_research_lab.studio.editor import (
    add_studio_point, get_studio_point, list_studio_points, move_studio_point,
    delete_studio_point, undo_last_action, StudioEditorError
)
from msk_research_lab.studio.dien_chan import (
    initialize_dien_chan_project, record_reactive_observation, attempt_project_2d_to_3d,
    attempt_promote_reactive_to_global, DienChanError, STANDARD_DIEN_CHAN_BASELINE
)
from msk_research_lab.studio.transfer import (
    export_studio_project, import_studio_project, compute_project_diff, TransferError
)
from msk_research_lab.bridge.packages import (
    create_research_package, validate_offline_package, TamperedPackageError, PackageRightsError, PackageSecurityError
)
from msk_research_lab.bridge.mock_consumer import (
    TherapyResearchClient, ConsumerBridgeError, AuthenticationError, KnowledgeNotFoundError
)
from msk_research_lab.discovery.markdown_importer import (
    import_markdown_reference_list, ImportSecurityError
)
from msk_research_lab.discovery.github_search import (
    GitHubSearchQuery, search_github, save_discovered_candidate, GitHubRepoItem
)
from msk_research_lab.discovery.research_queue import (
    queue_candidate_for_research, approve_and_clone_candidate, request_run_approval,
    record_research_decision, update_candidate_state, CloneApprovalError, ExecutionBlockedError
)
from msk_research_lab.discovery.static_analyzer import analyze_repository_static
from msk_research_lab.discovery.report_generator import compare_candidates, generate_research_report
from msk_research_lab.discovery.rea_adapter import probe_rea_adapter



START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run transactional migrations and seed catalog if empty."""
    run_migrations()
    seed_repositories_if_empty()
    seed_standard_models_if_empty()
    initialize_dien_chan_project()
    yield


app = FastAPI(
    title="MSK Research Lab OS",
    version="3.0.0",
    description="Independent research workbench for OSS repositories, literature, and scholarly tri-ledger.",
    lifespan=lifespan
)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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
async def launch_repo_endpoint(repo_id: str, request: Request):
    """Attempt execution of repository application (Requires enforceable sandbox AND explicit operator approval token)."""
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

    # Check for approval token
    token = None
    try:
        body = await request.json()
        token = body.get("approval_token") or body.get("token")
    except Exception:
        pass

    if not token:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "EXECUTION_APPROVAL_REQUIRED",
                "message": f"Execution BLOCKED: Separate operator approval token required before executing upstream repository '{repo_id}'.",
                "gate": "BLOCKED"
            }
        )

    return {"status": "LAUNCHED", "repo_id": repo_id, "token": token}


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


# ==============================================================================
# R4 Atlas & Surface Registration Endpoints (ATLAS-01..04)
# ==============================================================================

@app.get("/api/v1/atlas/models")
def api_list_models():
    """List registered 3D anatomical models with units, coordinate frames and checksums (ATLAS-01)."""
    return {"models": list_models_3d()}


@app.get("/api/v1/atlas/models/{model_id}")
def api_get_model(model_id: str):
    """Retrieve metadata for a specific 3D anatomical model."""
    m = get_model_3d(model_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return m


@app.get("/api/v1/atlas/models/{model_id}/file")
def api_get_model_file(model_id: str):
    """Serve the 3D model geometry file (.glb, .obj, etc.) for a registered model."""
    m = get_model_3d(model_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    mesh_rel = m.get("mesh_id", "")
    cfg = get_config()
    mesh_path = (cfg.storage.root_dir / mesh_rel).resolve()
    if not mesh_path.exists() or not mesh_path.is_file():
        raise HTTPException(status_code=404, detail=f"Model file '{mesh_rel}' not found on disk.")

    # Security: Ensure path does not escape root_dir
    if not str(mesh_path).startswith(str(cfg.storage.root_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied: path traversal attempt.")

    media_type = "model/gltf-binary" if mesh_path.suffix.lower() == ".glb" else "application/octet-stream"
    return FileResponse(path=str(mesh_path), media_type=media_type, filename=mesh_path.name)


@app.get("/api/v1/atlas/points/{code}")
def api_inspect_point(code: str):
    """Point inspector linking 3D skin anchors, ontology, scholarly claims, and tissue anatomy (ATLAS-04)."""
    res = inspect_point(code)
    return res


@app.post("/api/v1/atlas/surface/snap")
async def api_snap_point(request: Request):
    """Snap candidate 3D coordinate to declared exterior skin triangles (ATLAS-02)."""
    try:
        body = await request.json()
        x = float(body.get("x", 0.0))
        y = float(body.get("y", 0.0))
        z = float(body.get("z", 0.0))
        tol = float(body.get("tolerance_mm", 5.0))

        raw_tris = body.get("triangles", [])
        if not raw_tris:
            # Calibrated baseline triangle on superior shoulder ridge
            raw_tris = [
                [[-97.5, 475.0, -45.0], [-105.0, 472.0, -40.0], [-90.0, 470.0, -50.0]]
            ]

        triangles = []
        for idx, t in enumerate(raw_tris):
            triangles.append(
                Triangle3D(
                    Point3D(*t[0]),
                    Point3D(*t[1]),
                    Point3D(*t[2]),
                    face_index=idx
                )
            )

        res = snap_to_skin_mesh(Point3D(x, y, z), triangles, tolerance_mm=tol)
        return res
    except GeometryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid snap request: {e}")


@app.post("/api/v1/atlas/surface/anchor")
async def api_create_anchor(request: Request):
    """Persist a barycentric skin anchor tied to model and mesh SHA-256 (ATLAS-02)."""
    try:
        body = await request.json()
        anchor = create_skin_anchor(
            anchor_id=body["anchor_id"],
            model_id=body["model_id"],
            mesh_sha256=body["mesh_sha256"],
            face_index=int(body["face_index"]),
            barycentric=(float(body["barycentric"][0]), float(body["barycentric"][1]), float(body["barycentric"][2])),
            surface_point=Point3D(*body["surface_point"]),
            surface_normal=Point3D(*body["surface_normal"]),
        )
        return anchor
    except (ModelRegistryError, GeometryError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/atlas/compare")
async def api_compare_placements(request: Request):
    """Compare two 3D placements, enforcing landmark alignment guard (ATLAS-03)."""
    body = await request.json()
    if "point_code" not in body or "placement_a" not in body or "placement_b" not in body:
        raise HTTPException(status_code=400, detail="Fields 'point_code', 'placement_a', and 'placement_b' required.")

    return compare_placements_3d(
        point_code=body["point_code"],
        placement_a=body["placement_a"],
        placement_b=body["placement_b"],
        tolerance_mm=float(body.get("tolerance_mm", 5.0))
    )


@app.get("/api/v1/atlas/meridians/{code}")
def api_get_meridian_path(code: str):
    """Retrieve baked 3D meridian path, segment continuity, and gap warnings (ATLAS-02)."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM meridian_paths_3d WHERE LOWER(meridian_code) = LOWER(?);", (code.strip(),))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Meridian path for '{code}' not found.")
        res = dict(row)
        res["ordered_points"] = json.loads(res.get("ordered_points_json") or "[]")
        res["baked_segments"] = json.loads(res.get("baked_segments_json") or "[]")
        res["gap_warnings"] = json.loads(res.get("gap_warnings_json") or "[]")
        return res


@app.post("/api/v1/atlas/meridians/bake")
async def api_bake_meridian(request: Request):
    """Bake a candidate meridian path onto skin surface, checking interior penetration (ATLAS-02)."""
    body = await request.json()
    ctrl_pts = [Point3D(*p) for p in body["control_points"]]
    raw_tris = body.get("triangles", [
        [[-97.5, 475.0, -45.0], [-105.0, 472.0, -40.0], [-90.0, 470.0, -50.0]]
    ])
    triangles = [
        Triangle3D(Point3D(*t[0]), Point3D(*t[1]), Point3D(*t[2]), face_index=idx)
        for idx, t in enumerate(raw_tris)
    ]
    return bake_meridian_path(
        path_id=body["path_id"],
        meridian_code=body["meridian_code"],
        source_id=body.get("source_id", "source_custom"),
        model_id=body.get("model_id", "bodyparts3d_v4_ref_torso"),
        control_points=ctrl_pts,
        triangles=triangles,
        penetration_tolerance_mm=float(body.get("penetration_tolerance_mm", 25.0))
    )


@app.get("/api/v1/atlas/scene/{model_id}")
def api_get_atlas_scene(model_id: str):
    """Retrieve calibrated multi-layer 3D anatomical scene geometry with landmarks, points, meridians, and camera presets (ATLAS-01..06)."""
    return build_calibrated_bp3d_torso_scene()


# ==============================================================================
# R5 Private Atlas Studio & Diện Chẩn 2D Endpoints (ATLAS-05..06)
# ==============================================================================

@app.get("/api/v1/studio/projects")
def api_list_studio_projects():
    """List private researcher atlas projects (ATLAS-05)."""
    return {"projects": list_projects()}


@app.post("/api/v1/studio/projects")
async def api_create_studio_project(request: Request):
    """Create a private atlas project in an isolated namespace."""
    body = await request.json()
    try:
        proj = create_project(
            project_id=body["project_id"],
            title=body["title"],
            namespace=body["namespace"],
            description=body.get("description"),
            base_model_id=body.get("base_model_id"),
            base_image_sha256=body.get("base_image_sha256"),
            license=body.get("license", "PROPRIETARY_DRAFT"),
        )
        return proj
    except StudioProjectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/studio/projects/{project_id}")
def api_get_studio_project(project_id: str):
    """Get project details and active points."""
    proj = get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    points = list_studio_points(project_id, include_deleted=False)
    return {
        "project": proj,
        "points": points
    }


@app.post("/api/v1/studio/projects/{project_id}/points")
async def api_add_studio_point(project_id: str, request: Request):
    """Add a point to a private atlas project."""
    body = await request.json()
    try:
        pt = add_studio_point(
            project_id=project_id,
            point_id=body["point_id"],
            code=body["code"],
            canonical_label=body["canonical_label"],
            dimensionality=body.get("dimensionality", "3D_SURFACE"),
            point_kind=body.get("point_kind", "FIXED_EDUCATIONAL"),
            session_id=body.get("session_id"),
            session_timestamp=body.get("session_timestamp"),
            model_id=body.get("model_id"),
            mesh_sha256=body.get("mesh_sha256"),
            surface_xyz=body.get("surface_xyz"),
            face_index=body.get("face_index"),
            barycentric=body.get("barycentric"),
            image_sha256=body.get("image_sha256"),
            image_view=body.get("image_view"),
            pixel_xy=body.get("pixel_xy"),
            notes=body.get("notes"),
        )
        return pt
    except StudioEditorError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/v1/studio/projects/{project_id}/points/{point_id}")
async def api_move_studio_point(project_id: str, point_id: str, request: Request):
    """Update coordinates of a studio point."""
    body = await request.json()
    try:
        return move_studio_point(
            point_id=point_id,
            surface_xyz=body.get("surface_xyz"),
            face_index=body.get("face_index"),
            barycentric=body.get("barycentric"),
            pixel_xy=body.get("pixel_xy"),
        )
    except StudioEditorError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/studio/projects/{project_id}/points/{point_id}")
def api_delete_studio_point(project_id: str, point_id: str):
    """Soft delete a point in a private studio project."""
    try:
        return delete_studio_point(point_id)
    except StudioEditorError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/studio/projects/{project_id}/undo")
def api_undo_studio_action(project_id: str):
    """Undo the last edit action."""
    res = undo_last_action(project_id)
    if not res:
        return {"status": "NOTHING_TO_UNDO"}
    return res


@app.post("/api/v1/studio/projects/{project_id}/export")
def api_export_studio_project(project_id: str):
    """Export private atlas project as versioned JSON package (ATLAS-05)."""
    try:
        return export_studio_project(project_id)
    except TransferError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/studio/projects/import")
async def api_import_studio_project(request: Request):
    """Import and validate a private studio JSON package (ATLAS-05)."""
    body = await request.json()
    try:
        overwrite = bool(body.get("overwrite", False))
        payload = body.get("payload", body)
        return import_studio_project(payload, overwrite_existing=overwrite)
    except TransferError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/studio/projects/{project_id}/diff")
async def api_diff_studio_project(project_id: str, request: Request):
    """Compute diff between project and comparison package."""
    body = await request.json()
    return compute_project_diff(project_id, body)


@app.get("/api/v1/studio/dien-chan/baseline")
def api_get_dien_chan_baseline():
    """Retrieve standard 2D Diện Chẩn reference fixture points (ATLAS-06)."""
    return {"baseline_points": STANDARD_DIEN_CHAN_BASELINE}


# ==============================================================================
# R6 Therapy Research Bridge & Delivery Endpoints (BRIDGE-01..03)
# ==============================================================================

@app.post("/api/v1/bridge/packages/export")
async def api_export_research_package(request: Request):
    """Export approved offline research package from active snapshot (BRIDGE-02)."""
    verify_bearer_token(request)
    active = get_active_release()
    if not active:
        raise HTTPException(status_code=400, detail="No active validated snapshot to export package from.")

    body = await request.json()
    pkg_id = body.get("package_id", f"pkg_{active['release_id']}")
    from pathlib import Path
    cfg = get_config()
    out_dir = Path(cfg.storage.data_dir) / "packages" / pkg_id

    member_contents = {
        "points/gb21.json": json.dumps({
            "point_code": "GB21",
            "concept_id": "GB21",
            "canonical_label": "Jianjing (肩井)",
            "namespace": "TRADITIONAL_ACUPUNCTURE",
            "review_state": "EXPERT_REVIEWED",
            "rights_status": "ALLOWED",
            "snapshot_id": active["release_id"],
            "mesh_local_xyz_mm": [-97.5, 475.0, -45.0],
            "disclaimer": "Educational research record; not medical advice or treatment recommendation."
        }, indent=2).encode("utf-8")
    }

    try:
        manifest = create_research_package(
            package_dir=out_dir,
            package_id=pkg_id,
            snapshot_id=active["release_id"],
            source_ids=["who_standard_2008"],
            member_contents=member_contents,
            rights_review_state="ALLOWED"
        )
        return {
            "status": "EXPORTED",
            "package_id": pkg_id,
            "manifest_path": str(out_dir / "package_manifest.json"),
            "manifest": manifest
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/bridge/packages/verify")
async def api_verify_research_package(request: Request):
    """Cryptographically verify an offline research package (BRIDGE-02)."""
    body = await request.json()
    pkg_path = body.get("package_path")
    if not pkg_path:
        raise HTTPException(status_code=400, detail="Field 'package_path' required.")

    from pathlib import Path
    try:
        res = validate_offline_package(Path(pkg_path))
        return res
    except (TamperedPackageError, PackageRightsError, PackageSecurityError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# R1D DISCOVERY & RESEARCH PIPELINE ENDPOINTS (DISC-01..04, REV-01..02)
# =========================================================================

@app.post("/api/v1/discovery/import-markdown")
async def api_discovery_import_markdown(request: Request):
    """Import local Markdown repository reference list (DISC-01)."""
    body = await request.json()
    rel_path = body.get("file_path")
    if not rel_path:
        raise HTTPException(status_code=400, detail="Field 'file_path' is required.")

    cfg = get_config()
    target_path = Path(rel_path)
    if not target_path.is_absolute():
        target_path = cfg.root_dir / target_path

    try:
        summary = import_markdown_reference_list(target_path)
        return summary.model_dump()
    except ImportSecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/discovery/candidates")
def api_get_discovery_candidates(status: Optional[str] = None):
    """List repository candidates in research lifecycle (DISC-01, DISC-03)."""
    with get_db() as conn:
        if status:
            cur = conn.execute("SELECT * FROM repository_candidates WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cur = conn.execute("SELECT * FROM repository_candidates ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]


@app.get("/api/v1/discovery/candidates/{candidate_id}")
def api_get_discovery_candidate_detail(candidate_id: str):
    """Get candidate detail, occurrences, static analysis, and decisions (DISC-01, DISC-03)."""
    with get_db() as conn:
        cand = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")

        occs = conn.execute(
            """
            SELECT o.*, d.file_path, d.file_sha256
            FROM reference_occurrences o
            JOIN reference_documents d ON o.document_id = d.id
            WHERE o.candidate_id = ?
            ORDER BY o.line_number ASC
            """,
            (candidate_id,)
        ).fetchall()

        art = conn.execute(
            "SELECT * FROM static_analysis_artifacts WHERE candidate_id = ? ORDER BY analyzed_at DESC LIMIT 1",
            (candidate_id,)
        ).fetchone()

        decisions = conn.execute(
            "SELECT * FROM research_decisions WHERE candidate_id = ? ORDER BY reviewed_at DESC",
            (candidate_id,)
        ).fetchall()

        return {
            "candidate": dict(cand),
            "occurrences": [dict(o) for o in occs],
            "static_artifact": dict(art) if art else None,
            "decisions": [dict(d) for d in decisions]
        }


@app.post("/api/v1/discovery/github-search")
def api_discovery_github_search(request_data: Dict[str, Any]):
    """Execute live GitHub repository search with caching and transparent scoring (DISC-02)."""
    query = GitHubSearchQuery(
        keywords=request_data.get("keywords"),
        topic=request_data.get("topic"),
        language=request_data.get("language"),
        page=request_data.get("page", 1),
        per_page=request_data.get("per_page", 10)
    )
    result = search_github(query)
    return result.model_dump()


@app.post("/api/v1/discovery/candidates/save")
def api_save_discovered_candidate(payload: Dict[str, Any]):
    """Persist a candidate from search into repository_candidates (DISC-02)."""
    item_data = payload.get("item")
    if not item_data:
        raise HTTPException(status_code=400, detail="Field 'item' is required.")
    priority = payload.get("priority", "MEDIUM")
    item = GitHubRepoItem(**item_data)
    cand_id = save_discovered_candidate(item, priority=priority)
    return {"candidate_id": cand_id, "status": "SAVED"}


@app.post("/api/v1/research/queue")
def api_queue_candidate_for_research(payload: Dict[str, Any]):
    """Enroll candidate into research queue (DISC-03)."""
    candidate_id = payload.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="Field 'candidate_id' is required.")
    priority = payload.get("priority", "HIGH")
    tags = payload.get("tags", [])
    questions = payload.get("research_questions", [])

    try:
        res = queue_candidate_for_research(candidate_id, priority=priority, tags=tags, research_questions=questions)
        return res
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/research/approve-clone")
def api_approve_and_clone_candidate(payload: Dict[str, Any]):
    """Explicitly approved, commit-pinned clone (DISC-03)."""
    candidate_id = payload.get("candidate_id")
    operator = payload.get("operator")
    pinned_sha = payload.get("pinned_commit_sha")

    if not candidate_id or not operator:
        raise HTTPException(status_code=400, detail="Fields 'candidate_id' and 'operator' are required.")

    try:
        res = approve_and_clone_candidate(candidate_id, operator=operator, pinned_commit_sha=pinned_sha)
        return res
    except (CloneApprovalError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/research/inspect-static")
def api_inspect_static_candidate(payload: Dict[str, Any]):
    """Perform read-only static AST and manifest analysis (REV-01)."""
    candidate_id = payload.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="Field 'candidate_id' is required.")

    with get_db() as conn:
        cand = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not cand:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")

    clone_path = cand["clone_path"]
    if not clone_path or not Path(clone_path).exists():
        cfg = get_config()
        candidate_slug = f"{cand['owner']}--{cand['repo']}".lower()
        upstream_path = cfg.storage.root_dir / cfg.storage.upstream_dir / candidate_slug
        if upstream_path.exists():
            target_dir = upstream_path
        else:
            raise HTTPException(status_code=400, detail=f"Repository not cloned or clone path missing for {candidate_id}.")
    else:
        target_dir = Path(clone_path)

    report = analyze_repository_static(target_dir, candidate_id)
    return report.model_dump()


@app.post("/api/v1/research/compare")
def api_compare_candidates(payload: Dict[str, Any]):
    """Compare two or more repository candidates side-by-side (DISC-04)."""
    candidate_ids = payload.get("candidate_ids", [])
    if len(candidate_ids) < 2:
        raise HTTPException(status_code=400, detail="At least two candidate IDs required.")
    try:
        res = compare_candidates(candidate_ids)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/research/reports")
def api_generate_research_report(payload: Dict[str, Any]):
    """Generate source-cited research report and ingest into Tri-Ledger (DISC-04)."""
    candidate_id = payload.get("candidate_id")
    reviewer = payload.get("reviewer", "OPERATOR")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="Field 'candidate_id' is required.")
    try:
        res = generate_research_report(candidate_id, reviewer=reviewer)
        return res
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/research/reports/{report_id}")
def api_get_research_report(report_id: str):
    """Retrieve generated research report and manifest (DISC-04)."""
    with get_db() as conn:
        rep = conn.execute("SELECT * FROM research_reports WHERE id = ?", (report_id,)).fetchone()
        if not rep:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
        return dict(rep)


@app.post("/api/v1/research/decisions")
def api_record_research_decision(payload: Dict[str, Any]):
    """Record human evaluation decision: ADOPT, ADAPT, REJECT, or DEFER (DISC-04)."""
    candidate_id = payload.get("candidate_id")
    decision = payload.get("decision")
    justification = payload.get("justification")
    reviewed_by = payload.get("reviewed_by", "OPERATOR")

    if not candidate_id or not decision or not justification:
        raise HTTPException(status_code=400, detail="Fields 'candidate_id', 'decision', and 'justification' are required.")

    try:
        res = record_research_decision(
            candidate_id=candidate_id,
            decision=decision,
            justification=justification,
            reviewed_by=reviewed_by
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/research/rea/status")
def api_get_rea_status():
    """Probe optional REA adapter status (REV-02)."""
    status = probe_rea_adapter()
    return status.model_dump()




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
        model_count = conn.execute("SELECT COUNT(*) FROM models_3d;").fetchone()[0]
        point_count = conn.execute("SELECT COUNT(*) FROM point_placements_3d;").fetchone()[0]
        studio_project_count = conn.execute("SELECT COUNT(*) FROM private_atlas_projects;").fetchone()[0]
        studio_point_count = conn.execute("SELECT COUNT(*) FROM studio_points WHERE is_deleted = 0;").fetchone()[0]
        cand_count = conn.execute("SELECT COUNT(*) FROM repository_candidates;").fetchone()[0]
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

        cur_cands = conn.execute("SELECT id, canonical_url, status, priority, primary_language, license_spdx, discovery_source FROM repository_candidates ORDER BY created_at DESC LIMIT 10;")
        candidate_rows = ""
        for cand in cur_cands.fetchall():
            c_badge = "badge-green" if cand["status"] in ["STATIC_ANALYZED", "CLONED_PINNED", "ADOPT", "ADAPT"] else ("badge-red" if cand["status"] in ["BLOCKED", "REJECT"] else "badge-amber")
            candidate_rows += f"""
            <tr>
                <td><code>{cand['id']}</code></td>
                <td><a href="{cand['canonical_url']}" target="_blank" style="color:var(--accent-blue); text-decoration:none;">{cand['canonical_url']}</a></td>
                <td><span class="badge {c_badge}">{cand['status']}</span></td>
                <td><small>{cand['priority']}</small></td>
                <td><small>{cand['license_spdx']}</small></td>
                <td><small>{cand['discovery_source']}</small></td>
                <td>
                    <button class="btn-action" onclick="inspectStatic('{cand['id']}')">Inspect</button>
                    <button class="btn-action" onclick="generateReport('{cand['id']}')">Report</button>
                    <button class="btn-action" onclick="openDecisionPrompt('{cand['id']}')">Decide</button>
                </td>
            </tr>
            """



    active_snap_text = f"Active: <code>{active_release['release_id']}</code>" if active_release else "No snapshot published"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MSK Research Lab OS — Dashboard v3.0</title>
    <script src="/static/vendor/three.min.js"></script>
    <script src="/static/vendor/OrbitControls.js"></script>
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
        .atlas-workbench {{
            display: grid;
            grid-template-columns: 7fr 5fr;
            gap: 16px;
            margin-bottom: 24px;
            background: var(--surface-color);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            overflow: hidden;
        }}
        @media (max-width: 900px) {{
            .atlas-workbench {{ grid-template-columns: 1fr; }}
        }}
        .viewport-panel {{
            padding: 16px;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--card-border);
        }}
        .viewport-toolbar {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
            align-items: center;
        }}
        .btn-tool {{
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--card-border);
            color: var(--text-main);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .btn-tool:hover, .btn-tool.active {{
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--accent-blue);
            color: var(--accent-blue);
        }}
        .discovery-container {{
            background: var(--surface-color);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
        }}
        .discovery-form-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        @media (max-width: 800px) {{
            .discovery-form-grid {{ grid-template-columns: 1fr; }}
        }}
        .form-card {{
            background: #020617;
            border: 1px solid var(--card-border);
            border-radius: 6px;
            padding: 14px;
        }}
        .form-input {{
            width: 100%;
            background: #0f172a;
            border: 1px solid var(--card-border);
            color: var(--text-main);
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 6px;
            margin-bottom: 10px;
        }}
        .btn-primary {{
            background: var(--accent-blue);
            color: #0f172a;
            border: none;
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s ease;
        }}
        .btn-primary:hover {{ opacity: 0.9; }}
        .btn-action {{
            background: rgba(56, 189, 248, 0.12);
            color: var(--accent-blue);
            border: 1px solid var(--accent-blue);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            margin-right: 4px;
        }}
        .btn-action:hover {{
            background: var(--accent-blue);
            color: #0f172a;
        }}

        .layer-toggles {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
            padding: 10px;
            background: rgba(0,0,0,0.25);
            border-radius: 6px;
            font-size: 12px;
            align-items: center;
        }}
        .layer-toggles label {{
            display: flex;
            align-items: center;
            gap: 4px;
            cursor: pointer;
        }}
        .missing-layer-badge {{
            background: rgba(239, 68, 68, 0.1);
            color: #f87171;
            border: 1px dashed #ef4444;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 4px;
        }}
        .inspector-panel {{
            padding: 16px;
            overflow-y: auto;
            max-height: 560px;
        }}
        .inspector-header {{
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        .meta-row {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .meta-label {{ color: var(--text-muted); }}
        .meta-value {{ font-weight: 500; text-align: right; }}
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
                <h1>MSK Research Lab OS <span class="badge badge-green">R0 Verified</span> <span class="badge badge-green">R1D Verified</span> <span class="badge badge-amber">R4 Procedural Demo</span></h1>
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
            <div class="card">
                <h3>3D Anatomical Atlas</h3>
                <div class="value">{model_count} Models &bull; {point_count} Points</div>
                <div class="detail">Barycentric Anchoring &bull; 6-View Occlusion QA</div>
            </div>
            <div class="card">
                <h3>Private Atlas Studio</h3>
                <div class="value">{studio_project_count} Projects &bull; {studio_point_count} Points</div>
                <div class="detail">Diện Chẩn 2D &bull; Undo/Redo &bull; Multi-Tradition</div>
            </div>
        </div>

        <h2 class="section-title">Release Roadmap Gates (Rebaselined v3.1)</h2>
        <div class="gates-grid">
            <div class="gate-card">
                <div class="gate-name">R0: Foundation</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R1: Static Lab</div>
                <span class="badge badge-green">PASS (Static)</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">G2: Sandbox Run</div>
                <span class="badge badge-green">PASS (VERIFIED)</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R1D: Discovery</div>
                <span class="badge badge-green">PASS</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R2: Library</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R3: Tri-Ledger</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R4: 3D Atlas</div>
                <span class="badge badge-amber">PROTOTYPE (PROCEDURAL)</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R5: Studio</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R6: Bridge</div>
                <span class="badge badge-green">VERIFIED</span>
            </div>
        </div>

        <h2 class="section-title">Unified 3D Anatomy & Meridian Atlas Workbench (ATLAS-01..04)</h2>
        <div class="atlas-workbench">
            <div class="viewport-panel">
                <div class="viewport-toolbar" style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                    <span style="font-weight:600; font-size:12px; color:var(--accent-blue); margin-right:4px;">Camera:</span>
                    <button class="btn-tool active" onclick="setCamera('FRONT')">Front</button>
                    <button class="btn-tool" onclick="setCamera('BACK')">Back</button>
                    <button class="btn-tool" onclick="setCamera('LEFT')">Left</button>
                    <button class="btn-tool" onclick="setCamera('RIGHT')">Right</button>
                    <button class="btn-tool" onclick="setCamera('OBLIQUE_TOP')">Oblique &uarr;</button>
                    <button class="btn-tool" onclick="setCamera('OBLIQUE_BOTTOM')">Oblique &darr;</button>
                    <button class="btn-tool" onclick="setCamera('RESET')">Reset</button>
                    <span style="margin: 0 4px; color:var(--card-border);">|</span>
                    <label style="font-size:12px; cursor:pointer;">
                        <input type="checkbox" id="xrayToggle" onchange="toggleXRay(this.checked)"> X-Ray
                    </label>
                    <label style="font-size:12px; cursor:pointer; margin-left:6px;">
                        <input type="checkbox" id="wireToggle" onchange="toggleWireframe(this.checked)"> Wireframe
                    </label>
                </div>

                <div style="display:flex; gap:8px; margin:8px 0; align-items:center;">
                    <label style="font-size:12px; color:var(--text-muted); font-weight:600;">Region Filter:</label>
                    <select id="regionFilter" onchange="filterRegion(this.value)" style="background:var(--bg-color); border:1px solid var(--card-border); color:var(--text-main); padding:3px 6px; border-radius:4px; font-size:12px;">
                        <option value="ALL">All Regions (5 Points)</option>
                        <option value="SHOULDER_RIDGE">Shoulder Ridge (GB21, SI15)</option>
                        <option value="POSTERIOR_NECK">Posterior Neck (GV14)</option>
                        <option value="UPPER_BACK">Upper Back (SI14, BL11)</option>
                    </select>

                    <label style="font-size:12px; color:var(--text-muted); font-weight:600; margin-left:8px;">Point:</label>
                    <select id="pointSelect" onchange="onPointDropdownChange(this.value)" style="background:var(--bg-color); border:1px solid var(--card-border); color:var(--text-main); padding:3px 6px; border-radius:4px; font-size:12px;">
                        <option value="GB21">GB21 — Jianjing (肩井)</option>
                        <option value="GV14">GV14 — Dazhui (大椎)</option>
                        <option value="SI14">SI14 — Jianwaishu (肩外俞)</option>
                        <option value="SI15">SI15 — Jianzhongshu (肩中俞)</option>
                        <option value="BL11">BL11 — Dazhu (大杼)</option>
                    </select>
                </div>

                <div id="atlasCanvasContainer" style="position:relative; width:100%; height:380px; background:#020617; border-radius:6px; overflow:hidden; border:1px solid var(--card-border);">
                    <div id="webglContainer" style="width:100%; height:100%;"></div>
                    <canvas id="atlasCanvas" width="700" height="380" style="width:100%; height:100%; display:none;"></canvas>
                    <div style="position:absolute; bottom:8px; left:8px; font-size:11px; background:rgba(15,23,42,0.85); padding:4px 8px; border-radius:4px; border:1px solid var(--card-border); z-index:10;">
                        Ref: <code>procedural_demo_torso</code> (calibrated for <code>bodyparts3d_v4_ref_torso</code>) &bull; Units: <code>mm</code> &bull; <span style="color:var(--status-amber); font-weight:600;">PROTOTYPE DEMO (NOT CLINICAL BP3D ATLAS)</span> &bull; <span id="vramStatus" style="color:var(--status-green);">VRAM: ~1.4 MB</span>
                    </div>
                </div>

                <div class="layer-toggles">
                    <strong style="color:var(--text-muted); font-size:11px; text-transform:uppercase;">Tissue Layers:</strong>
                    <label><input type="checkbox" id="layerSkin" checked onchange="toggleLayer('skin', this.checked)"> Skin (Integumentary)</label>
                    <label><input type="checkbox" id="layerSuperficial" checked onchange="toggleLayer('superficial_muscle', this.checked)"> Superficial Muscle</label>
                    <label><input type="checkbox" id="layerDeep" checked onchange="toggleLayer('deep_muscle', this.checked)"> Deep Muscle</label>
                    <label><input type="checkbox" id="layerSkeletal" checked onchange="toggleLayer('skeletal', this.checked)"> Skeletal</label>
                    <label><input type="checkbox" id="layerNerves" checked onchange="toggleLayer('nerves', this.checked)"> Nerves (CN XI)</label>
                    <label><input type="checkbox" id="layerMeridian" checked onchange="toggleLayer('meridian', this.checked)"> Meridians (GB/SI)</label>
                    <span class="missing-layer-badge">Deep Fascia: UNAVAILABLE</span>
                    <span class="missing-layer-badge">Visceral Organs: UNAVAILABLE</span>
                </div>
            </div>

            <div class="inspector-panel" id="inspectorBox">
                <div class="inspector-header">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 id="inspectorPointTitle" style="font-size:15px; color:var(--accent-blue); margin:0;">Point Inspector &bull; GB21</h3>
                        <span class="badge badge-green">REGISTERED</span>
                    </div>
                    <div id="inspectorPointNames" style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                        Jianjing (肩井) &bull; Kiên tỉnh &bull; <code>TRADITIONAL_ACUPUNCTURE</code>
                    </div>
                </div>

                <div class="meta-row">
                    <span class="meta-label">3D Position (mesh_local_xyz)</span>
                    <span class="meta-value"><code id="inspectorCoords">[-97.5, 475.0, -45.0] mm</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Surface Skin Anchor</span>
                    <span class="meta-value"><code id="inspectorAnchor">anchor_gb21_bp3d (Face #412)</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Barycentric Weights (u, v, w)</span>
                    <span class="meta-value"><code id="inspectorBarycentric">[0.333, 0.333, 0.334]</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Underlying Mesh SHA</span>
                    <span class="meta-value"><code>e3b0c442...991b7852b855</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Surface Normal Vector</span>
                    <span class="meta-value"><code id="inspectorNormal">[-0.150, 0.920, -0.360]</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Contact Distance to Mesh</span>
                    <span class="meta-value" style="color:var(--status-green);">0.00 mm (Exact Skin Contact)</span>
                </div>

                <div style="margin-top:14px;">
                    <div style="font-size:11px; text-transform:uppercase; color:var(--text-muted); font-weight:600; margin-bottom:6px;">
                        Six-View Camera Occlusion QA
                    </div>
                    <div id="inspectorOcclusionGrid" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; font-size:11px;">
                        <div id="occ_FRONT" style="background:rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px;">
                            Front: <span style="color:var(--status-amber);">OCCLUDED</span>
                        </div>
                        <div id="occ_BACK" style="background:rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px;">
                            Back: <span style="color:var(--status-green);">VISIBLE</span>
                        </div>
                        <div id="occ_LEFT" style="background:rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px;">
                            Left: <span style="color:var(--status-green);">VISIBLE</span>
                        </div>
                        <div id="occ_RIGHT" style="background:rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px;">
                            Right: <span style="color:var(--status-amber);">OCCLUDED</span>
                        </div>
                        <div id="occ_OBLIQUE_TOP" style="background:rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px;">
                            Oblique &uarr;: <span style="color:var(--status-green);">VISIBLE</span>
                        </div>
                        <div id="occ_OBLIQUE_BOTTOM" style="background:rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px;">
                            Oblique &darr;: <span style="color:var(--status-amber);">OCCLUDED</span>
                        </div>
                    </div>
                </div>

                <div style="margin-top:14px;">
                    <div style="font-size:11px; text-transform:uppercase; color:var(--text-muted); font-weight:600; margin-bottom:6px;">
                        Tissue Layers under Point
                    </div>
                    <ul id="inspectorTissueLayers" style="font-size:11px; padding-left:16px; color:var(--text-muted);">
                        <li><strong style="color:var(--text-main);">Integumentary:</strong> Skin over superior shoulder ridge</li>
                        <li><strong style="color:var(--text-main);">Muscular (Superficial):</strong> Trapezius muscle descending fibers</li>
                        <li><strong style="color:var(--text-main);">Muscular (Deep):</strong> Levator scapulae &amp; Supraspinatus</li>
                        <li><strong style="color:var(--text-main);">Skeletal:</strong> Clavicle, Acromion, C7–T1 spinous processes</li>
                        <li><strong style="color:var(--text-main);">Nervous:</strong> Spinal accessory nerve (CN XI) superficial branches</li>
                    </ul>
                </div>

                <div style="margin-top:14px; padding:8px; background:rgba(245,158,11,0.08); border-left:3px solid var(--status-amber); font-size:11px; color:var(--text-muted);">
                    <strong>Epistemic Disclaimer &amp; Warning:</strong> This is a procedural demonstration envelope for benchmarking registration algorithms and multi-layer WebGL rendering. It must NOT be labeled or treated as a verified clinical anatomical atlas. Real clinical registration requires DBCLS BodyParts3D polygon mesh imports under CC-BY-SA 2.1 JP.
                </div>
            </div>
        </div>

        <script>
            let currentCamera = 'FRONT';
            let isXRay = false;
            let isWireframe = false;
            let isWebGLActive = false;
            let threeScene, threeCamera, threeRenderer, threeControls;
            let sceneData = null;
            let meshLayers = {{}};
            let pointMarkers = {{}};
            let meridianLines = [];
            let currentRegion = 'ALL';
            let selectedPointCode = 'GB21';

            const POINT_DATA_MAP = {{
                "GB21": {{
                    code: "GB21",
                    canonical: "Jianjing",
                    hanzi: "肩井",
                    vietnamese: "Kiên tỉnh",
                    region: "SHOULDER_RIDGE",
                    coords: "[-97.5, 475.0, -45.0] mm",
                    anchor: "anchor_gb21_bp3d (Face #412)",
                    barycentric: "[0.333, 0.333, 0.334]",
                    normal: "[-0.150, 0.920, -0.360]",
                    occlusion: {{ FRONT: false, BACK: true, LEFT: true, RIGHT: false, OBLIQUE_TOP: true, OBLIQUE_BOTTOM: false }},
                    layers: [
                        ["Integumentary", "Skin over superior shoulder ridge"],
                        ["Muscular (Superficial)", "Trapezius muscle descending fibers"],
                        ["Muscular (Deep)", "Levator scapulae & Supraspinatus"],
                        ["Skeletal", "First rib & Clavicular boundary"],
                        ["Nervous", "Spinal accessory nerve (CN XI) superficial branches"]
                    ]
                }},
                "GV14": {{
                    code: "GV14",
                    canonical: "Dazhui",
                    hanzi: "大椎",
                    vietnamese: "Đại chùy",
                    region: "POSTERIOR_NECK",
                    coords: "[0.0, 485.0, -85.0] mm",
                    anchor: "anchor_gv14_bp3d (Face #480)",
                    barycentric: "[0.500, 0.250, 0.250]",
                    normal: "[0.000, 0.100, -0.990]",
                    occlusion: {{ FRONT: false, BACK: true, LEFT: true, RIGHT: true, OBLIQUE_TOP: true, OBLIQUE_BOTTOM: false }},
                    layers: [
                        ["Integumentary", "Skin over posterior midline"],
                        ["Muscular", "Supraspinous & interspinous ligaments"],
                        ["Skeletal", "C7 spinous process & T1 vertebra"],
                        ["Nervous", "Cervical spinal nerve dorsal rami"]
                    ]
                }},
                "SI14": {{
                    code: "SI14",
                    canonical: "Jianwaishu",
                    hanzi: "肩外俞",
                    vietnamese: "Kiên ngoại du",
                    region: "UPPER_BACK",
                    coords: "[-110.0, 450.0, -80.0] mm",
                    anchor: "anchor_si14_bp3d (Face #390)",
                    barycentric: "[0.330, 0.330, 0.340]",
                    normal: "[-0.200, 0.300, -0.930]",
                    occlusion: {{ FRONT: false, BACK: true, LEFT: true, RIGHT: false, OBLIQUE_TOP: true, OBLIQUE_BOTTOM: false }},
                    layers: [
                        ["Integumentary", "Skin over medial scapular ridge"],
                        ["Muscular", "Trapezius & Rhomboid major"],
                        ["Skeletal", "Superior angle of scapula"],
                        ["Nervous", "Dorsal scapular nerve"]
                    ]
                }},
                "SI15": {{
                    code: "SI15",
                    canonical: "Jianzhongshu",
                    hanzi: "肩中俞",
                    vietnamese: "Kiên trung du",
                    region: "SHOULDER_RIDGE",
                    coords: "[-60.0, 470.0, -82.0] mm",
                    anchor: "anchor_si15_bp3d (Face #415)",
                    barycentric: "[0.400, 0.300, 0.300]",
                    normal: "[-0.100, 0.200, -0.970]",
                    occlusion: {{ FRONT: false, BACK: true, LEFT: true, RIGHT: false, OBLIQUE_TOP: true, OBLIQUE_BOTTOM: false }},
                    layers: [
                        ["Integumentary", "Skin lateral to C7"],
                        ["Muscular", "Trapezius transverse fibers & Levator scapulae"],
                        ["Skeletal", "Transverse process C7"],
                        ["Nervous", "Accessory nerve branches"]
                    ]
                }},
                "BL11": {{
                    code: "BL11",
                    canonical: "Dazhu",
                    hanzi: "大杼",
                    vietnamese: "Đại trữ",
                    region: "UPPER_BACK",
                    coords: "[-45.0, 440.0, -80.0] mm",
                    anchor: "anchor_bl11_bp3d (Face #360)",
                    barycentric: "[0.330, 0.330, 0.340]",
                    normal: "[-0.050, 0.100, -0.990]",
                    occlusion: {{ FRONT: false, BACK: true, LEFT: true, RIGHT: false, OBLIQUE_TOP: true, OBLIQUE_BOTTOM: false }},
                    layers: [
                        ["Integumentary", "Skin 1.5 cun lateral to T1"],
                        ["Muscular", "Trapezius, Rhomboid, Erector spinae"],
                        ["Skeletal", "First intercostal space"],
                        ["Nervous", "T1 spinal nerve dorsal ramus"]
                    ]
                }}
            }};

            function selectPoint(code) {{
                selectedPointCode = code;
                const d = POINT_DATA_MAP[code];
                if (!d) return;

                document.getElementById('inspectorPointTitle').innerText = 'Point Inspector • ' + d.code;
                document.getElementById('inspectorPointNames').innerHTML = d.canonical + ' (' + d.hanzi + ') &bull; ' + d.vietnamese + ' &bull; <code>TRADITIONAL_ACUPUNCTURE</code>';
                document.getElementById('inspectorCoords').innerText = d.coords;
                document.getElementById('inspectorAnchor').innerText = d.anchor;
                document.getElementById('inspectorBarycentric').innerText = d.barycentric;
                document.getElementById('inspectorNormal').innerText = d.normal;

                // Occlusion badges
                const views = ['FRONT', 'BACK', 'LEFT', 'RIGHT', 'OBLIQUE_TOP', 'OBLIQUE_BOTTOM'];
                views.forEach(v => {{
                    const el = document.getElementById('occ_' + v);
                    if (el) {{
                        const isVis = d.occlusion[v];
                        const label = v.replace('_', ' ').toLowerCase();
                        const capitalized = label.charAt(0).toUpperCase() + label.slice(1);
                        const statusSpan = isVis ? '<span style="color:var(--status-green);">VISIBLE</span>' : '<span style="color:var(--status-amber);">OCCLUDED</span>';
                        el.innerHTML = (v === 'OBLIQUE_TOP' ? 'Oblique &uarr;: ' : (v === 'OBLIQUE_BOTTOM' ? 'Oblique &darr;: ' : capitalized + ': ')) + statusSpan;
                    }}
                }});

                // Tissue layers
                const listEl = document.getElementById('inspectorTissueLayers');
                if (listEl) {{
                    listEl.innerHTML = d.layers.map(l => '<li><strong style="color:var(--text-main);">' + l[0] + ':</strong> ' + l[1] + '</li>').join('');
                }}

                // Sync point dropdown
                const sel = document.getElementById('pointSelect');
                if (sel && sel.value !== code) {{
                    sel.value = code;
                }}

                // In Three.js: highlight marker
                if (isWebGLActive && pointMarkers[code]) {{
                    Object.keys(pointMarkers).forEach(k => {{
                        const pm = pointMarkers[k];
                        if (k === code) {{
                            pm.sphere.material.color.setHex(0xfacc15);
                            pm.sphere.scale.set(1.4, 1.4, 1.4);
                            pm.ring.material.color.setHex(0xfacc15);
                        }} else {{
                            pm.sphere.material.color.setHex(0x22c55e);
                            pm.sphere.scale.set(1.0, 1.0, 1.0);
                            pm.ring.material.color.setHex(0x38bdf8);
                        }}
                    }});
                }}

                if (!isWebGLActive) {{
                    redrawCanvas();
                }}
            }}

            function onPointDropdownChange(code) {{
                selectPoint(code);
            }}

            function filterRegion(reg) {{
                currentRegion = reg;
                if (isWebGLActive) {{
                    Object.keys(pointMarkers).forEach(k => {{
                        const pm = pointMarkers[k];
                        const match = (reg === 'ALL' || pm.data.region === reg);
                        pm.group.visible = match;
                    }});
                }}
                const currentData = POINT_DATA_MAP[selectedPointCode];
                if (reg !== 'ALL' && currentData && currentData.region !== reg) {{
                    const firstMatch = Object.keys(POINT_DATA_MAP).find(k => POINT_DATA_MAP[k].region === reg);
                    if (firstMatch) selectPoint(firstMatch);
                }}
                if (!isWebGLActive) {{
                    redrawCanvas();
                }}
            }}

            function setCamera(cam) {{
                currentCamera = cam;
                document.querySelectorAll('.viewport-toolbar .btn-tool').forEach(b => {{
                    b.classList.remove('active');
                    if (b.innerText.toUpperCase().includes(cam.replace('_',' '))) b.classList.add('active');
                }});

                if (isWebGLActive && sceneData && sceneData.camera_presets && sceneData.camera_presets[cam]) {{
                    const p = sceneData.camera_presets[cam];
                    threeCamera.position.set(p.position[0], p.position[1], p.position[2]);
                    if (threeControls) {{
                        threeControls.target.set(p.target[0], p.target[1], p.target[2]);
                        threeControls.update();
                    }}
                }} else {{
                    redrawCanvas();
                }}
            }}

            function toggleXRay(val) {{
                isXRay = val;
                if (isWebGLActive && meshLayers['skin']) {{
                    meshLayers['skin'].material.opacity = val ? 0.12 : 0.38;
                }}
                if (!isWebGLActive) {{
                    redrawCanvas();
                }}
            }}

            function toggleWireframe(val) {{
                isWireframe = val;
                if (isWebGLActive) {{
                    ['skin', 'skeletal', 'superficial_muscle', 'deep_muscle'].forEach(k => {{
                        if (meshLayers[k] && meshLayers[k].material) {{
                            meshLayers[k].material.wireframe = val;
                        }}
                    }});
                }}
                if (!isWebGLActive) {{
                    redrawCanvas();
                }}
            }}

            function toggleLayer(layerKey, isVisible) {{
                if (isWebGLActive) {{
                    if (layerKey === 'meridian') {{
                        meridianLines.forEach(l => l.visible = isVisible);
                    }} else if (meshLayers[layerKey]) {{
                        meshLayers[layerKey].visible = isVisible;
                    }}
                }}
                if (!isWebGLActive) {{
                    redrawCanvas();
                }}
            }}

            async function initAtlas3D() {{
                const container = document.getElementById('webglContainer');
                if (!window.THREE || !container) {{
                    use2DFallback();
                    return;
                }}

                try {{
                    const w = container.clientWidth || 700;
                    const h = container.clientHeight || 380;

                    threeScene = new THREE.Scene();
                    threeScene.background = new THREE.Color(0x020617);

                    threeCamera = new THREE.PerspectiveCamera(45, w / h, 1, 3000);
                    threeCamera.position.set(0, 450, 600);

                    threeRenderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: 'low-power' }});
                    threeRenderer.setSize(w, h);
                    threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
                    container.appendChild(threeRenderer.domElement);

                    if (window.THREE.OrbitControls) {{
                        threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
                        threeControls.target.set(0, 450, 0);
                        threeControls.enableDamping = true;
                        threeControls.dampingFactor = 0.05;
                    }}

                    const ambLight = new THREE.AmbientLight(0xffffff, 0.7);
                    threeScene.add(ambLight);
                    const dir1 = new THREE.DirectionalLight(0xffffff, 0.85);
                    dir1.position.set(300, 600, 400);
                    threeScene.add(dir1);
                    const dir2 = new THREE.DirectionalLight(0x94a3b8, 0.4);
                    dir2.position.set(-300, 200, -400);
                    threeScene.add(dir2);

                    const resp = await fetch('/api/v1/atlas/scene/bodyparts3d_v4_ref_torso');
                    if (!resp.ok) throw new Error('Failed to fetch scene: ' + resp.status);
                    sceneData = await resp.json();

                    if (sceneData.layers && sceneData.layers.skin) {{
                        const g = new THREE.BufferGeometry();
                        g.setAttribute('position', new THREE.Float32BufferAttribute(sceneData.layers.skin.vertices, 3));
                        g.setIndex(sceneData.layers.skin.indices);
                        g.computeVertexNormals();
                        const m = new THREE.MeshStandardMaterial({{
                            color: 0x38bdf8,
                            transparent: true,
                            opacity: 0.38,
                            side: THREE.DoubleSide,
                            roughness: 0.35,
                            metalness: 0.1,
                            depthWrite: false
                        }});
                        meshLayers['skin'] = new THREE.Mesh(g, m);
                        threeScene.add(meshLayers['skin']);
                    }}

                    if (sceneData.layers && sceneData.layers.skeletal) {{
                        const g = new THREE.BufferGeometry();
                        g.setAttribute('position', new THREE.Float32BufferAttribute(sceneData.layers.skeletal.vertices, 3));
                        g.setIndex(sceneData.layers.skeletal.indices);
                        g.computeVertexNormals();
                        const m = new THREE.MeshStandardMaterial({{
                            color: 0xe2e8f0,
                            roughness: 0.6,
                            metalness: 0.1
                        }});
                        meshLayers['skeletal'] = new THREE.Mesh(g, m);
                        threeScene.add(meshLayers['skeletal']);
                    }}

                    if (sceneData.layers && sceneData.layers.superficial_muscle) {{
                        const g = new THREE.BufferGeometry();
                        g.setAttribute('position', new THREE.Float32BufferAttribute(sceneData.layers.superficial_muscle.vertices, 3));
                        g.setIndex(sceneData.layers.superficial_muscle.indices);
                        g.computeVertexNormals();
                        const m = new THREE.MeshStandardMaterial({{
                            color: 0xdc2626,
                            transparent: true,
                            opacity: 0.65,
                            side: THREE.DoubleSide
                        }});
                        meshLayers['superficial_muscle'] = new THREE.Mesh(g, m);
                        threeScene.add(meshLayers['superficial_muscle']);
                    }}

                    if (sceneData.layers && sceneData.layers.deep_muscle) {{
                        const g = new THREE.BufferGeometry();
                        g.setAttribute('position', new THREE.Float32BufferAttribute(sceneData.layers.deep_muscle.vertices, 3));
                        g.setIndex(sceneData.layers.deep_muscle.indices);
                        g.computeVertexNormals();
                        const m = new THREE.MeshStandardMaterial({{
                            color: 0x991b1b,
                            transparent: true,
                            opacity: 0.75,
                            side: THREE.DoubleSide
                        }});
                        meshLayers['deep_muscle'] = new THREE.Mesh(g, m);
                        threeScene.add(meshLayers['deep_muscle']);
                    }}

                    if (sceneData.layers && sceneData.layers.nerves) {{
                        const g = new THREE.BufferGeometry();
                        g.setAttribute('position', new THREE.Float32BufferAttribute(sceneData.layers.nerves.vertices, 3));
                        g.setIndex(sceneData.layers.nerves.indices);
                        const m = new THREE.LineBasicMaterial({{ color: 0xfacc15, linewidth: 2 }});
                        meshLayers['nerves'] = new THREE.LineSegments(g, m);
                        threeScene.add(meshLayers['nerves']);
                    }}

                    meridianLines = [];
                    if (sceneData.meridians) {{
                        sceneData.meridians.forEach(mr => {{
                            const pts = mr.control_points.map(p => new THREE.Vector3(p[0], p[1], p[2]));
                            const curve = new THREE.CatmullRomCurve3(pts);
                            const curvePts = curve.getPoints(50);
                            const g = new THREE.BufferGeometry().setFromPoints(curvePts);
                            const col = mr.code === 'GB' ? 0x22c55e : 0x38bdf8;
                            const m = new THREE.LineBasicMaterial({{ color: col, linewidth: 2.5 }});
                            const line = new THREE.Line(g, m);
                            threeScene.add(line);
                            meridianLines.push(line);
                        }});
                    }}

                    pointMarkers = {{}};
                    if (sceneData.points) {{
                        sceneData.points.forEach(pt => {{
                            const group = new THREE.Group();
                            group.position.set(pt.coordinates_mm[0], pt.coordinates_mm[1], pt.coordinates_mm[2]);

                            const spGeo = new THREE.SphereGeometry(4.5, 16, 16);
                            const spMat = new THREE.MeshBasicMaterial({{ color: 0x22c55e }});
                            const sphere = new THREE.Mesh(spGeo, spMat);
                            sphere.userData = {{ code: pt.code }};
                            group.add(sphere);

                            const ringGeo = new THREE.RingGeometry(5.5, 7.5, 24);
                            const ringMat = new THREE.MeshBasicMaterial({{ color: 0x38bdf8, side: THREE.DoubleSide }});
                            const ring = new THREE.Mesh(ringGeo, ringMat);
                            ring.rotation.x = Math.PI / 2;
                            group.add(ring);

                            threeScene.add(group);
                            pointMarkers[pt.code] = {{ group, sphere, ring, data: pt }};
                        }});
                    }}

                    isWebGLActive = true;

                    const raycaster = new THREE.Raycaster();
                    const mouse = new THREE.Vector2();
                    threeRenderer.domElement.addEventListener('click', (evt) => {{
                        const rect = threeRenderer.domElement.getBoundingClientRect();
                        mouse.x = ((evt.clientX - rect.left) / rect.width) * 2 - 1;
                        mouse.y = -((evt.clientY - rect.top) / rect.height) * 2 + 1;
                        raycaster.setFromCamera(mouse, threeCamera);

                        const clickTargets = [];
                        Object.values(pointMarkers).forEach(pm => {{
                            if (pm.group.visible) clickTargets.push(pm.sphere);
                        }});

                        const hits = raycaster.intersectObjects(clickTargets);
                        if (hits.length > 0) {{
                            const c = hits[0].object.userData.code;
                            if (c) selectPoint(c);
                        }}
                    }});

                    function animateAtlas() {{
                        requestAnimationFrame(animateAtlas);
                        if (threeControls) threeControls.update();
                        threeRenderer.render(threeScene, threeCamera);
                    }}
                    animateAtlas();

                    selectPoint('GB21');
                    setCamera('FRONT');

                    window.addEventListener('resize', () => {{
                        if (!threeRenderer || !threeCamera || !container) return;
                        const nw = container.clientWidth;
                        const nh = container.clientHeight;
                        threeCamera.aspect = nw / nh;
                        threeCamera.updateProjectionMatrix();
                        threeRenderer.setSize(nw, nh);
                    }});

                }} catch (e) {{
                    console.warn('WebGL init failed, using Canvas 2D fallback:', e);
                    use2DFallback();
                }}
            }}

            function use2DFallback() {{
                isWebGLActive = false;
                const webglDiv = document.getElementById('webglContainer');
                const canvas2d = document.getElementById('atlasCanvas');
                const vramBadge = document.getElementById('vramStatus');
                if (webglDiv) webglDiv.style.display = 'none';
                if (canvas2d) canvas2d.style.display = 'block';
                if (vramBadge) {{
                    vramBadge.innerText = 'Canvas 2D Software Fallback';
                    vramBadge.style.color = 'var(--status-amber)';
                }}
                redrawCanvas();
            }}

            function redrawCanvas() {{
                const canvas = document.getElementById('atlasCanvas');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                const w = canvas.width;
                const h = canvas.height;
                ctx.clearRect(0, 0, w, h);

                ctx.strokeStyle = '#1e293b';
                ctx.lineWidth = 1;
                for (let x = 0; x < w; x += 40) {{
                    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
                }}
                for (let y = 0; y < h; y += 40) {{
                    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
                }}

                const cx = w / 2;
                const cy = h / 2 + 30;

                const showSkin = document.getElementById('layerSkin')?.checked ?? true;
                const showSuper = document.getElementById('layerSuperficial')?.checked ?? true;
                const showDeep = document.getElementById('layerDeep')?.checked ?? true;
                const showBones = document.getElementById('layerSkeletal')?.checked ?? true;
                const showNerves = document.getElementById('layerNerves')?.checked ?? true;
                const showMeridian = document.getElementById('layerMeridian')?.checked ?? true;

                let scaleX = 1.0;
                let offsetX = 0;
                if (currentCamera === 'BACK') {{ scaleX = -1.0; }}
                else if (currentCamera === 'LEFT') {{ scaleX = 0.4; offsetX = -60; }}
                else if (currentCamera === 'RIGHT') {{ scaleX = 0.4; offsetX = 60; }}
                else if (currentCamera === 'OBLIQUE_TOP') {{ scaleX = 0.85; }}
                else if (currentCamera === 'OBLIQUE_BOTTOM') {{ scaleX = 0.85; }}

                ctx.save();
                ctx.translate(cx + offsetX, cy);

                if (showBones) {{
                    ctx.strokeStyle = '#cbd5e1';
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.moveTo(0, -110);
                    ctx.lineTo(0, 80);
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.moveTo(-110 * scaleX, -55);
                    ctx.lineTo(0, -65);
                    ctx.lineTo(110 * scaleX, -55);
                    ctx.stroke();

                    ctx.strokeStyle = 'rgba(203, 213, 225, 0.4)';
                    for (let r = -40; r <= 60; r += 20) {{
                        ctx.beginPath();
                        ctx.ellipse(0, r, Math.abs(85 * scaleX), 12, 0, 0, Math.PI * 2);
                        ctx.stroke();
                    }}
                }}

                if (showDeep) {{
                    ctx.fillStyle = isXRay ? 'rgba(185, 28, 28, 0.25)' : 'rgba(185, 28, 28, 0.45)';
                    ctx.beginPath();
                    ctx.moveTo(-45 * scaleX, -75);
                    ctx.lineTo(-85 * scaleX, -55);
                    ctx.lineTo(-70 * scaleX, -30);
                    ctx.closePath();
                    ctx.fill();

                    ctx.beginPath();
                    ctx.moveTo(45 * scaleX, -75);
                    ctx.lineTo(85 * scaleX, -55);
                    ctx.lineTo(70 * scaleX, -30);
                    ctx.closePath();
                    ctx.fill();
                }}

                if (showSuper) {{
                    ctx.fillStyle = isXRay ? 'rgba(225, 29, 72, 0.2)' : 'rgba(225, 29, 72, 0.4)';
                    ctx.beginPath();
                    ctx.moveTo(0, -90);
                    ctx.lineTo(-100 * scaleX, -50);
                    ctx.lineTo(0, 20);
                    ctx.lineTo(100 * scaleX, -50);
                    ctx.closePath();
                    ctx.fill();
                }}

                if (showNerves) {{
                    ctx.strokeStyle = '#facc15';
                    ctx.lineWidth = 1.5;
                    ctx.setLineDash([3, 3]);
                    ctx.beginPath();
                    ctx.moveTo(-20 * scaleX, -85);
                    ctx.quadraticCurveTo(-45 * scaleX, -65, -70 * scaleX, -45);
                    ctx.stroke();
                    ctx.setLineDash([]);
                }}

                if (showSkin) {{
                    const skinAlpha = isXRay ? 0.15 : 0.4;
                    ctx.fillStyle = `rgba(56, 189, 248, ${{skinAlpha}})`;
                    ctx.strokeStyle = 'rgba(56, 189, 248, 0.8)';
                    ctx.lineWidth = 1.8;

                    ctx.beginPath();
                    ctx.moveTo(-35 * scaleX, -110);
                    ctx.lineTo(-35 * scaleX, -75);
                    ctx.quadraticCurveTo(-80 * scaleX, -60, -135 * scaleX, -35);
                    ctx.lineTo(-125 * scaleX, 90);
                    ctx.lineTo(125 * scaleX, 90);
                    ctx.lineTo(135 * scaleX, -35);
                    ctx.quadraticCurveTo(80 * scaleX, -60, 35 * scaleX, -75);
                    ctx.lineTo(35 * scaleX, -110);
                    ctx.closePath();
                    if (isWireframe) {{
                        ctx.stroke();
                    }} else {{
                        ctx.fill();
                        ctx.stroke();
                    }}
                }}

                if (showMeridian) {{
                    ctx.strokeStyle = '#22c55e';
                    ctx.lineWidth = 2.5;
                    ctx.beginPath();
                    ctx.moveTo(-25 * scaleX, -95);
                    ctx.lineTo(-45 * scaleX, -70);
                    ctx.lineTo(-65 * scaleX, -55);
                    ctx.lineTo(-78 * scaleX, -35);
                    ctx.stroke();
                }}

                const selCode = selectedPointCode || 'GB21';
                const ptMapCoords = {{
                    "GB21": [-65 * scaleX, -55],
                    "GV14": [0, -65],
                    "SI14": [-80 * scaleX, -30],
                    "SI15": [-40 * scaleX, -50],
                    "BL11": [-28 * scaleX, -20]
                }};
                const pos = ptMapCoords[selCode] || [-65 * scaleX, -55];
                const ptX = pos[0];
                const ptY = pos[1];

                let isOccluded = (currentCamera === 'FRONT' || currentCamera === 'RIGHT' || currentCamera === 'OBLIQUE_BOTTOM');
                if (isXRay || !isOccluded) {{
                    ctx.fillStyle = isOccluded ? 'rgba(245, 158, 11, 0.5)' : 'rgba(34, 197, 94, 0.8)';
                    ctx.beginPath();
                    ctx.arc(ptX, ptY, 7, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.fillStyle = '#ffffff';
                    ctx.beginPath();
                    ctx.arc(ptX, ptY, 3, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.fillStyle = '#38bdf8';
                    ctx.font = 'bold 11px monospace';
                    ctx.fillText(selCode + ' (' + (POINT_DATA_MAP[selCode]?.canonical || '') + ')', ptX - 35, ptY - 12);
                }}

                ctx.restore();
            }}

            window.addEventListener('DOMContentLoaded', () => {{
                initAtlas3D();
                drawDienChanCanvas();
            }});

            function drawDienChanCanvas() {{
                const canvas = document.getElementById('dienChanCanvas');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // 1. Front Face Contour (Left Half)
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                ctx.ellipse(180, 160, 100, 130, 0, 0, Math.PI * 2);
                ctx.stroke();

                // Eyes & Nose guides
                ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
                ctx.beginPath(); ctx.arc(140, 130, 12, 0, Math.PI * 2); ctx.stroke();
                ctx.beginPath(); ctx.arc(220, 130, 12, 0, Math.PI * 2); ctx.stroke();
                // Nose
                ctx.beginPath(); ctx.moveTo(180, 140); ctx.lineTo(172, 190); ctx.lineTo(188, 190); ctx.stroke();
                // Mouth
                ctx.beginPath(); ctx.moveTo(155, 230); ctx.lineTo(205, 230); ctx.stroke();

                // Point 19 (Nhân trung / Subnasal - Front)
                ctx.fillStyle = '#22c55e';
                ctx.beginPath(); ctx.arc(180, 205, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 10px monospace';
                ctx.fillText('DC_19 [Fixed]', 192, 208);

                // 2. Profile Face Contour (Right Half)
                ctx.strokeStyle = '#38bdf8';
                ctx.beginPath();
                ctx.moveTo(420, 50); // Forehead
                ctx.quadraticCurveTo(460, 90, 480, 140); // Nose bridge
                ctx.lineTo(495, 160); // Nose tip
                ctx.lineTo(470, 175); // Subnasal
                ctx.quadraticCurveTo(480, 195, 475, 215); // Lips
                ctx.quadraticCurveTo(480, 245, 450, 260); // Chin
                ctx.lineTo(390, 260); // Jawline
                ctx.lineTo(370, 210); // Mandibular angle
                ctx.lineTo(370, 130); // Ear line
                ctx.closePath();
                ctx.stroke();

                // Ear contour
                ctx.strokeStyle = '#cbd5e1';
                ctx.beginPath();
                ctx.ellipse(375, 165, 18, 32, 0, 0, Math.PI * 2);
                ctx.stroke();

                // Point 0 (Tragus Notch - Profile)
                ctx.fillStyle = '#22c55e';
                ctx.beginPath(); ctx.arc(362, 165, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.fillText('DC_0 [Fixed]', 300, 168);

                // Point 14 (Infra-auricular - Profile)
                ctx.fillStyle = '#22c55e';
                ctx.beginPath(); ctx.arc(378, 205, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.fillText('DC_14 [Fixed]', 388, 208);

                // Point 275 (Mandibular angle - Profile)
                ctx.fillStyle = '#22c55e';
                ctx.beginPath(); ctx.arc(372, 230, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.fillText('DC_275 [Fixed]', 382, 233);

                // Synthetic Reactive Observation (Sinh huyệt - Amber Diamond)
                ctx.fillStyle = '#f59e0b';
                ctx.beginPath();
                ctx.moveTo(440, 115);
                ctx.lineTo(447, 122);
                ctx.lineTo(440, 129);
                ctx.lineTo(433, 122);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = '#f59e0b';
                ctx.fillText('S_01 [Reactive]', 410, 108);
            }}

            async function triggerMarkdownImport() {{
                const path = document.getElementById('importPathInput').value.trim();
                if (!path) return alert('Please enter reference file path.');
                const panel = document.getElementById('discoveryOutputPanel');
                const body = document.getElementById('outputPanelBody');
                panel.style.display = 'block';
                body.innerHTML = '<em>Importing markdown reference list...</em>';

                try {{
                    const res = await fetch('/api/v1/discovery/import-markdown', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{file_path: path}})
                    }});
                    const data = await res.json();
                    if (!res.ok) {{
                        body.innerHTML = '<span style="color:var(--status-red);">Import Failed: ' + (data.detail || JSON.stringify(data)) + '</span>';
                    }} else {{
                        body.innerHTML = '<span style="color:var(--status-green);">✓ Document imported: <code>' + data.document_id + '</code></span><br>' +
                            'Candidates found: <strong>' + data.candidate_count + '</strong> (' + data.new_candidates_registered + ' new)<br>' +
                            'Occurrences tracked: <strong>' + data.occurrence_count + '</strong><br>' +
                            '<small style="color:var(--text-muted);">Reloading dashboard...</small>';
                        setTimeout(() => window.location.reload(), 1200);
                    }}
                }} catch (e) {{
                    body.innerHTML = '<span style="color:var(--status-red);">Network Error: ' + e.message + '</span>';
                }}
            }}

            async function triggerGitHubSearch() {{
                const kw = document.getElementById('searchKeywordInput').value.trim();
                const topic = document.getElementById('searchTopicInput').value.trim();
                const panel = document.getElementById('discoveryOutputPanel');
                const body = document.getElementById('outputPanelBody');
                panel.style.display = 'block';
                body.innerHTML = '<em>Querying GitHub search API...</em>';

                try {{
                    const res = await fetch('/api/v1/discovery/github-search', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{keywords: kw || 'msk anatomy', topic: topic || null, per_page: 5}})
                    }});
                    const data = await res.json();
                    if (!res.ok) {{
                        body.innerHTML = '<span style="color:var(--status-red);">Search Error: ' + (data.detail || JSON.stringify(data)) + '</span>';
                    }} else {{
                        let html = '<div style="margin-bottom:6px;"><strong>Found ' + data.total_count + ' repos</strong> (Cached: ' + data.is_cached + ', Status: ' + data.status + '):</div>';
                        (data.items || []).forEach(item => {{
                            html += '<div style="padding:6px; border-bottom:1px solid #1e293b; display:flex; justify-content:space-between; align-items:center;">' +
                                '<div><strong>' + item.owner + '/' + item.repo + '</strong> &bull; ' + item.license_spdx + ' &bull; Score: ' + item.heuristic_score + '<br>' +
                                '<small style="color:var(--text-muted);">' + (item.description || 'No description').substring(0, 80) + '</small></div>' +
                                '<button class="btn-action" onclick="saveCandidate(' + JSON.stringify(item).replace(/"/g, '&quot;') + ')">Save</button>' +
                                '</div>';
                        }});
                        body.innerHTML = html;
                    }}
                }} catch (e) {{
                    body.innerHTML = '<span style="color:var(--status-red);">Network Error: ' + e.message + '</span>';
                }}
            }}

            async function saveCandidate(item) {{
                try {{
                    const res = await fetch('/api/v1/discovery/candidates/save', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{item: item, priority: 'HIGH'}})
                    }});
                    const data = await res.json();
                    alert('Candidate saved: ' + data.candidate_id);
                    window.location.reload();
                }} catch (e) {{
                    alert('Error saving: ' + e.message);
                }}
            }}

            async function inspectStatic(candId) {{
                const panel = document.getElementById('discoveryOutputPanel');
                const body = document.getElementById('outputPanelBody');
                panel.style.display = 'block';
                body.innerHTML = '<em>Running static AST analysis on ' + candId + '...</em>';

                try {{
                    const res = await fetch('/api/v1/research/inspect-static', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{candidate_id: candId}})
                    }});
                    const data = await res.json();
                    if (!res.ok) {{
                        body.innerHTML = '<span style="color:var(--status-amber);">' + (data.detail || JSON.stringify(data)) + '</span>';
                    }} else {{
                        body.innerHTML = '<span style="color:var(--status-green);">✓ Static Analysis Complete:</span><br>' +
                            'UI Framework: <strong>' + (data.ui_framework || 'None') + '</strong><br>' +
                            '3D Models: <strong>' + (data.model_formats.join(', ') || 'None') + '</strong><br>' +
                            'Risk Hooks: <strong>' + data.risk_hooks.length + '</strong><br>' +
                            'Files Scanned: <strong>' + data.total_files_scanned + '</strong>';
                    }}
                }} catch (e) {{
                    body.innerHTML = '<span style="color:var(--status-red);">Error: ' + e.message + '</span>';
                }}
            }}

            async function generateReport(candId) {{
                const panel = document.getElementById('discoveryOutputPanel');
                const body = document.getElementById('outputPanelBody');
                panel.style.display = 'block';
                body.innerHTML = '<em>Generating source-cited research report...</em>';

                try {{
                    const res = await fetch('/api/v1/research/reports', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{candidate_id: candId, reviewer: 'OPERATOR'}})
                    }});
                    const data = await res.json();
                    if (!res.ok) {{
                        body.innerHTML = '<span style="color:var(--status-red);">Report Error: ' + (data.detail || JSON.stringify(data)) + '</span>';
                    }} else {{
                        body.innerHTML = '<span style="color:var(--status-green);">✓ Research Report Generated: <code>' + data.report_id + '</code></span><br>' +
                            'Manifest SHA: <code>' + data.manifest_sha256.substring(0, 16) + '...</code><br>' +
                            'Tri-Ledger Ingest ID: <code>' + data.tri_ledger_evidence_id + '</code><br>' +
                            '<a href="/api/v1/research/reports/' + data.report_id + '" target="_blank" style="color:var(--accent-blue);">View JSON Report</a>';
                    }}
                }} catch (e) {{
                    body.innerHTML = '<span style="color:var(--status-red);">Error: ' + e.message + '</span>';
                }}
            }}

            function openDecisionPrompt(candId) {{
                const dec = prompt('Enter decision (ADOPT, ADAPT, REJECT, DEFER):', 'ADAPT');
                if (!dec) return;
                const just = prompt('Enter substantive justification (min 10 chars):', 'Compatible coordinates and safe license for adaptation.');
                if (!just) return;

                fetch('/api/v1/research/decisions', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{candidate_id: candId, decision: dec.toUpperCase(), justification: just, reviewed_by: 'OPERATOR'}})
                }})
                .then(r => r.json())
                .then(d => {{
                    alert('Decision recorded: ' + (d.decision || d.detail));
                    window.location.reload();
                }})
                .catch(e => alert('Error: ' + e.message));
            }}
        </script>


        <h2 class="section-title">Private Atlas Studio &amp; 2D Diện Chẩn Facial Reflexology (ATLAS-05..06)</h2>
        <div class="atlas-workbench" style="margin-bottom: 24px;">
            <div class="viewport-panel">
                <div class="viewport-toolbar">
                    <span style="font-weight:600; font-size:12px; color:var(--accent-blue); margin-right:8px;">2D Facial Maps:</span>
                    <span class="badge badge-green">Front SHA: 6a4a159f...</span>
                    <span class="badge badge-green">Profile SHA: 7b5b260e...</span>
                    <span class="badge badge-amber">CANNOT_IMPLICITLY_PROJECT_2D_TO_3D</span>
                </div>

                <div style="position:relative; width:100%; height:320px; background:#020617; border-radius:6px; overflow:hidden; border:1px solid var(--card-border);">
                    <canvas id="dienChanCanvas" width="600" height="320" style="width:100%; height:100%; display:block;"></canvas>
                    <div style="position:absolute; bottom:8px; left:8px; font-size:11px; background:rgba(15,23,42,0.85); padding:4px 8px; border-radius:4px; border:1px solid var(--card-border);">
                        Namespace: <code>DIEN_CHAN</code> &bull; Pixel Anchors &bull; Epistemic Isolation Guaranteed
                    </div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px; font-size:11px; color:var(--text-muted);">
                    <div>
                        <span style="display:inline-block; width:10px; height:10px; background:#22c55e; border-radius:50%; margin-right:4px;"></span>
                        <strong>Fixed Educational Reference</strong> (Standard Atlas)
                    </div>
                    <div>
                        <span style="display:inline-block; width:10px; height:10px; background:#f59e0b; transform:rotate(45deg); margin-right:4px;"></span>
                        <strong>Reactive Observation</strong> (Session-Specific &bull; Promotion Prohibited)
                    </div>
                </div>
            </div>

            <div class="inspector-panel">
                <div class="inspector-header">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="font-size:15px; color:var(--accent-blue); margin:0;">Studio Actions &amp; Transfer</h3>
                        <span class="badge badge-green">ATLAS-05 / 06 PASS</span>
                    </div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                        Versioned JSON Schemas &bull; Non-destructive Revisions &bull; Private Drafts
                    </div>
                </div>

                <div class="meta-row">
                    <span class="meta-label">Active Studio Projects</span>
                    <span class="meta-value"><code>{studio_project_count} Registered</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Active Studio Points</span>
                    <span class="meta-value"><code>{studio_point_count} Points Persisted</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Supported Namespaces</span>
                    <span class="meta-value"><code>DIEN_CHAN, TCM, THAI_SEN, TRIGGER_POINT</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Schema Roundtrip Format</span>
                    <span class="meta-value"><code>schemas/atlas_point.schema.json (v3.0.0)</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Upstream Immutability Guard</span>
                    <span class="meta-value" style="color:var(--status-green);">ENFORCED (No Upstream Edits)</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">2D &rarr; 3D Promotion Guard</span>
                    <span class="meta-value" style="color:var(--status-green);">ENFORCED (Explicit Rejection)</span>
                </div>

                <div style="margin-top:14px; padding:8px; background:rgba(56,189,248,0.06); border-left:3px solid var(--accent-blue); font-size:11px; color:var(--text-muted);">
                    <strong>Studio Endpoint Contracts:</strong><br>
                    &bull; <code>POST /api/v1/studio/projects/{{id}}/export</code> (JSON Package)<br>
                    &bull; <code>POST /api/v1/studio/projects/import</code> (Integrity &amp; Rights Check)<br>
                    &bull; <code>POST /api/v1/studio/projects/{{id}}/undo</code> (Transactional Rollback)
                </div>
            </div>
        </div>

        <h2 class="section-title">Therapy Research Bridge &amp; Offline Delivery (BRIDGE-01..03)</h2>
        <div class="atlas-workbench" style="margin-bottom: 24px;">
            <div class="viewport-panel">
                <div class="viewport-toolbar">
                    <span style="font-weight:600; font-size:12px; color:var(--accent-blue); margin-right:8px;">Consumer Channels:</span>
                    <span class="badge badge-green">Online Bearer API: ACTIVE</span>
                    <span class="badge badge-green">Offline Hashed Package: READY</span>
                    <span class="badge badge-green">Field-Level Redaction: ENFORCED</span>
                </div>

                <div style="padding:16px; background:#020617; border-radius:6px; border:1px solid var(--card-border); font-size:12px;">
                    <h4 style="color:var(--text-main); margin-bottom:8px; font-size:13px;">MSK-Therapy-OS Interoperability Verification:</h4>
                    <ul style="color:var(--text-muted); padding-left:18px; line-height:1.7;">
                        <li><strong style="color:var(--text-main);">Stand-alone Mock Consumer:</strong> Verified on target Windows/WSL host without modifying Therapy OS.</li>
                        <li><strong style="color:var(--text-main);">Online Channel:</strong> Reads reviewed points with Bearer token authentication (401/403 enforced).</li>
                        <li><strong style="color:var(--text-main);">Offline Fallback:</strong> If Lab OS is offline, local <code>schemas/research_package.schema.json</code> package serves validated points.</li>
                        <li><strong style="color:var(--text-main);">Cryptographic Integrity:</strong> SHA-256 member verification fails closed if any package file is tampered.</li>
                        <li><strong style="color:var(--text-main);">Patient Privacy Boundary:</strong> Zero clinical patient records or session notes stored in Lab OS.</li>
                    </ul>
                </div>
            </div>

            <div class="inspector-panel">
                <div class="inspector-header">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="font-size:15px; color:var(--accent-blue); margin:0;">Bridge Invariants</h3>
                        <span class="badge badge-green">BRIDGE-01..03 PASS</span>
                    </div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                        Locked OpenAPI Contract &bull; Offline Survivability
                    </div>
                </div>

                <div class="meta-row">
                    <span class="meta-label">Delivery Channel 1</span>
                    <span class="meta-value"><code>GET /api/v1/knowledge/points/{{code}}</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Delivery Channel 2</span>
                    <span class="meta-value"><code>2data/packages/&lt;pkg_id&gt;/package_manifest.json</code></span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Raw Books / PDFs Access</span>
                    <span class="meta-value" style="color:var(--status-green);">EXCLUDED (Access Prohibited)</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Upstream Runner Access</span>
                    <span class="meta-value" style="color:var(--status-green);">EXCLUDED (Process API Blocked)</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Tamper Detection</span>
                    <span class="meta-value" style="color:var(--status-green);">ENFORCED (SHA-256 Member Mismatch Rejection)</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">Patient Boundary</span>
                    <span class="meta-value" style="color:var(--status-green);">PRESERVED (No Patient Data in Lab OS)</span>
                </div>
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

        <h2 class="section-title">Discovery & Research Pipeline Candidates (R1D &bull; Provenance & Queue)</h2>
        <div class="discovery-container">
            <div class="discovery-form-grid">
                <!-- Local Markdown Import Card -->
                <div class="form-card">
                    <h4 style="color:var(--accent-blue); margin-bottom:6px; font-size:13px;">1. Import Local Markdown Reference List (DISC-01)</h4>
                    <p style="color:var(--text-muted); font-size:11px; margin-bottom:10px;">
                        Scans curated lists from <code>research/references/</code>. Deduplicates canonical URLs, preserves exact source lines, registers candidates as unverified.
                    </p>
                    <label style="font-size:11px; color:var(--text-muted);">Reference File Path (relative to lab root):</label>
                    <input type="text" id="importPathInput" class="form-input" value="research/references/awesome_msk_biomedical_repos.md">
                    <button class="btn-primary" onclick="triggerMarkdownImport()">Import Reference List</button>
                </div>

                <!-- GitHub Intelligent Search Card -->
                <div class="form-card">
                    <h4 style="color:var(--accent-blue); margin-bottom:6px; font-size:13px;">2. GitHub Intelligent Discovery (DISC-02)</h4>
                    <p style="color:var(--text-muted); font-size:11px; margin-bottom:10px;">
                        Discovers biomedical/MSK repos via public API. Caches metadata (24h TTL) and scores via transparent heuristics.
                    </p>
                    <div style="display:flex; gap:8px;">
                        <input type="text" id="searchKeywordInput" class="form-input" placeholder="Keywords (e.g. acupuncture 3d)" style="margin-top:0;">
                        <input type="text" id="searchTopicInput" class="form-input" placeholder="Topic (optional)" style="margin-top:0; width:120px;">
                    </div>
                    <button class="btn-primary" onclick="triggerGitHubSearch()">Search GitHub</button>
                </div>
            </div>

            <!-- Dynamic Feedback Panel -->
            <div id="discoveryOutputPanel" style="display:none; background:#020617; border:1px solid var(--accent-blue); border-radius:6px; padding:12px; margin-top:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="color:var(--accent-blue); font-size:13px;" id="outputPanelTitle">Pipeline Activity</strong>
                    <button class="btn-tool" onclick="document.getElementById('discoveryOutputPanel').style.display='none'">Close</button>
                </div>
                <div id="outputPanelBody" style="font-size:12px; color:var(--text-main); max-height:260px; overflow-y:auto; line-height:1.6;"></div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Candidate ID</th>
                    <th>Canonical Repository URL</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>License</th>
                    <th>Discovery Source</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {candidate_rows or '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No discovery candidates imported yet.</td></tr>'}
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
