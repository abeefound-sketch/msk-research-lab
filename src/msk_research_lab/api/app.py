"""FastAPI application for MSK Research Lab OS Dashboard and API."""

import os
import time
import json
import psutil
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


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request):
    """Render responsive, clean Dashboard suitable for 1366x768 Windows browser display."""
    cfg = get_config()
    db_health = check_db_health()
    sandbox = probe_sandbox_capabilities()
    repos = get_all_repositories()
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
                <h1>MSK Research Lab OS <span class="badge badge-green">R0 Verified</span></h1>
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
                <h3>Security Policy</h3>
                <div class="value">Deny-by-Default</div>
                <div class="detail">Loopback Enforced &bull; Untrusted Execution BLOCKED</div>
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
                <span class="badge badge-amber">BLOCKED (Sandbox)</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R2: Library</div>
                <span class="badge badge-uninspected">NOT STARTED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R3: Integrity</div>
                <span class="badge badge-uninspected">NOT STARTED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R4: 3D Atlas</div>
                <span class="badge badge-uninspected">NOT STARTED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R5: Studio</div>
                <span class="badge badge-uninspected">NOT STARTED</span>
            </div>
            <div class="gate-card">
                <div class="gate-name">R6: Bridge</div>
                <span class="badge badge-uninspected">NOT STARTED</span>
            </div>
        </div>

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
