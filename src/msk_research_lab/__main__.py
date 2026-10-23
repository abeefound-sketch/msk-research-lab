"""CLI entrypoint for MSK Research Lab OS."""

import argparse
import json
import os
import platform
import shutil
import socket
import sys
import time
from pathlib import Path

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import check_db_health, get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.sandbox.probe import probe_sandbox_capabilities


def run_doctor_checks() -> dict:
    """Collect verifiable environment diagnostics."""
    cfg = get_config()

    # 1. Platform and kernel
    uname = platform.uname()
    is_wsl = "microsoft" in uname.release.lower() or "wsl" in uname.release.lower()

    # 2. Python and SQLite FTS5
    import sqlite3
    with sqlite3.connect(":memory:") as mem_conn:
        has_fts5 = bool(mem_conn.execute("SELECT 1 FROM pragma_compile_options WHERE compile_options='ENABLE_FTS5'").fetchall())

    # 3. Memory via /proc/meminfo or psutil
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_info = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent
        }
    except Exception:
        mem_info = {"error": "psutil unavailable"}

    # 4. Storage free space
    disk_c = shutil.disk_usage("/mnt/c") if os.path.exists("/mnt/c") else shutil.disk_usage(".")
    disk_d = shutil.disk_usage("/mnt/d") if os.path.exists("/mnt/d") else None

    # 5. Tool availability
    tools = {
        "git": shutil.which("git"),
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "podman": shutil.which("podman"),
        "docker": shutil.which("docker")
    }

    # 6. Database and migrations
    db_status = check_db_health()

    # 7. Sandbox isolation probe
    sandbox_probe = probe_sandbox_capabilities()

    # 8. Check 4 source specs presence
    spec_dir = Path("1docs/specs")
    specs_present = {}
    for spec_name in [
        "MSK_RESEARCH_LAB_OS_SPEC_v1.0.md",
        "MSK_Research_Lab_OS_Engineering_Spec.md",
        "MSK_Research_Lab_OS_MVP_v2_SPEC.md",
        "MSK_Research_Lab_OS_v2.1_Engineering_SPEC.md"
    ]:
        p = spec_dir / spec_name
        specs_present[spec_name] = p.exists()

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "release": "R0",
        "environment": {
            "system": uname.system,
            "release": uname.release,
            "machine": uname.machine,
            "is_wsl2": is_wsl,
            "python_version": platform.python_version(),
            "sqlite_version": sqlite3.sqlite_version,
            "fts5_enabled": has_fts5
        },
        "resources": {
            "memory": mem_info,
            "disk_c_free_gb": round(disk_c.free / (1024**3), 2),
            "disk_c_total_gb": round(disk_c.total / (1024**3), 2),
            "disk_d_free_gb": round(disk_d.free / (1024**3), 2) if disk_d else None
        },
        "tools": tools,
        "database": db_status,
        "sandbox": sandbox_probe,
        "specs_verified": specs_present,
        "target_port": cfg.server.port,
        "loopback_host": cfg.server.host
    }


def cmd_doctor(args):
    """Execute environment doctor check."""
    results = run_doctor_checks()

    if getattr(args, "json_output", False):
        print(json.dumps(results, indent=2))
        return 0

    print("==================================================")
    print("      MSK Research Lab OS v3.0 — Doctor Check     ")
    print("==================================================")
    env = results["environment"]
    print(f"✓ OS: {env['system']} {env['release']} ({env['machine']}) - WSL2: {env['is_wsl2']}")
    print(f"✓ Python: {env['python_version']} | SQLite: {env['sqlite_version']} (FTS5: {env['fts5_enabled']})")

    res = results["resources"]
    mem = res["memory"]
    print(f"✓ RAM: {mem.get('total_gb')} GB total, {mem.get('available_gb')} GB available")
    print(f"✓ Disk C: {res['disk_c_free_gb']} GB free of {res['disk_c_total_gb']} GB")
    if res['disk_d_free_gb'] is not None:
        print(f"✓ Disk D: {res['disk_d_free_gb']} GB free (low space constraint)")

    tools = results["tools"]
    print(f"✓ Git: {tools['git'] or 'NOT FOUND'}")
    print(f"✓ Node: {tools['node'] or 'NOT FOUND'} | npm: {tools['npm'] or 'NOT FOUND'}")

    sb = results["sandbox"]
    print(f"! Sandbox Isolation: {sb['status']} (Gate: {sb['readiness_gate']})")
    print(f"  Note: {sb['details']}")

    db = results["database"]
    print(f"✓ Database: WAL={db['wal_mode']}, FKs={db['fk_enabled']}, Migrations=v{db['schema_version']}")

    # Save to evidence if directory exists
    evidence_dir = Path("2data/evidence")
    if evidence_dir.exists():
        with open(evidence_dir / "R0_doctor.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"✓ Diagnostic report saved to: {evidence_dir}/R0_doctor.json")

    return 0


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def cmd_serve(args):
    """Start local web dashboard and read-only API on 127.0.0.1:8091."""
    import uvicorn
    cfg = get_config()
    host = args.host or cfg.server.host
    port = args.port or cfg.server.port

    if is_port_in_use(port, host):
        print(f"ERROR: Port {port} on {host} is already in use by another process.")
        print(f"Please stop the conflicting process or choose an alternate port.")
        return 1

    print(f"==================================================")
    print(f"  Starting MSK Research Lab OS on http://{host}:{port}")
    print(f"  Target: Windows Browser (1366x768 friendly)     ")
    print(f"  Press Ctrl+C to stop cleanly.                   ")
    print(f"==================================================")

    # Automatically run migrations on startup
    run_migrations()

    uvicorn.run(
        "msk_research_lab.api.app:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="info"
    )
    return 0


def cmd_migrate(args):
    """Run transactional migrations."""
    applied = run_migrations()
    if applied:
        print(f"Successfully applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("Database is already up to date.")
    return 0


# =========================================================================
# R1D Discovery & Research CLI Handlers
# =========================================================================

def cmd_discovery(args):
    """Discovery subcommands: import-md, search-github, list."""
    from msk_research_lab.discovery.markdown_importer import import_markdown_reference_list
    from msk_research_lab.discovery.github_search import GitHubSearchQuery, search_github

    action = getattr(args, "discovery_action", None)
    if action == "import-md":
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = get_config().root_dir / file_path
        summary = import_markdown_reference_list(file_path)
        print(f"✓ Markdown list imported: {summary.document_id}")
        print(f"  File SHA-256: {summary.file_sha256[:16]}...")
        print(f"  Candidates found: {summary.candidate_count} ({summary.new_candidates_registered} new)")
        print(f"  Occurrences tracked: {summary.occurrence_count}")
        if summary.skipped_invalid_urls:
            print(f"  Skipped {len(summary.skipped_invalid_urls)} invalid/malicious URLs")
        return 0

    elif action == "search-github":
        query = GitHubSearchQuery(keywords=args.query, topic=args.topic, language=args.language)
        result = search_github(query)
        print(f"GitHub Search: '{result.query_text}' (Status: {result.status}, Cached: {result.is_cached})")
        print(f"Total matching: {result.total_count}")
        for item in result.items:
            print(f" - [{item.license_spdx}] {item.canonical_url} (Stars: {item.stars_count}, Score: {item.heuristic_score})")
            if item.description:
                print(f"   {item.description[:90]}")
        return 0

    elif action == "list":
        with get_db() as conn:
            cur = conn.execute("SELECT id, canonical_url, status, priority, license_spdx FROM repository_candidates ORDER BY created_at DESC")
            cands = cur.fetchall()
            print(f"Total repository candidates: {len(cands)}")
            for c in cands:
                print(f" - {c['id']}: {c['canonical_url']} [{c['status']}] (Priority: {c['priority']}, License: {c['license_spdx']})")
        return 0

    else:
        print("Usage: msk-lab discovery {import-md,search-github,list}")
        return 1


def cmd_research(args):
    """Research subcommands: queue, inspect-static, compare, report, decision, rea-status."""
    from msk_research_lab.discovery.research_queue import queue_candidate_for_research, record_research_decision
    from msk_research_lab.discovery.static_analyzer import analyze_repository_static
    from msk_research_lab.discovery.report_generator import compare_candidates, generate_research_report
    from msk_research_lab.discovery.rea_adapter import probe_rea_adapter

    action = getattr(args, "research_action", None)
    if action == "queue":
        res = queue_candidate_for_research(args.repo_id, priority=args.priority)
        print(f"✓ Candidate {res['candidate_id']} enrolled in research queue (Status: {res['status']}, Priority: {res['priority']})")
        return 0

    elif action == "inspect-static":
        with get_db() as conn:
            cand = conn.execute("SELECT * FROM repository_candidates WHERE id = ?", (args.repo_id,)).fetchone()
            if not cand:
                print(f"Error: Candidate '{args.repo_id}' not found.")
                return 1

        clone_path = cand["clone_path"]
        if not clone_path or not Path(clone_path).exists():
            cfg = get_config()
            candidate_slug = f"{cand['owner']}--{cand['repo']}".lower()
            upstream_path = cfg.storage.root_dir / cfg.storage.upstream_dir / candidate_slug
            if upstream_path.exists():
                target_dir = upstream_path
            else:
                print(f"Error: Candidate '{args.repo_id}' is not cloned locally. Please clone before static inspection.")
                return 1
        else:
            target_dir = Path(clone_path)

        report = analyze_repository_static(target_dir, args.repo_id)
        print(f"✓ Static Analysis completed for {args.repo_id} (Commit: {report.commit_sha[:8]})")
        print(f"  UI Framework: {report.ui_framework}")
        print(f"  3D Models: {', '.join(report.model_formats) if report.model_formats else 'None'}")
        print(f"  Risk Hooks: {len(report.risk_hooks)}")
        return 0

    elif action == "compare":
        res = compare_candidates(args.repo_ids)
        print(f"Candidate Comparison ({res['compared_candidates_count']} items):")
        matrix = res["comparison_matrix"]
        print("Licenses:", json.dumps(matrix["licenses"], indent=2))
        print("UI Frameworks:", json.dumps(matrix["ui_frameworks"], indent=2))
        print("Hardware Readiness:", json.dumps(matrix["hardware_readiness"], indent=2))
        return 0

    elif action == "report":
        res = generate_research_report(args.repo_id, reviewer=getattr(args, "reviewer", "OPERATOR"))
        print(f"✓ Scholarly research report generated: {res['report_id']}")
        print(f"  Directory: {res['report_dir']}")
        print(f"  Manifest SHA-256: {res['manifest_sha256']}")
        print(f"  Tri-Ledger Evidence ID: {res['tri_ledger_evidence_id']}")
        return 0

    elif action == "decision":
        res = record_research_decision(args.repo_id, args.decision, args.justification, reviewed_by=getattr(args, "reviewer", "OPERATOR"))
        print(f"✓ Decision recorded: {res['candidate_id']} -> {res['decision']} by {res['reviewed_by']}")
        return 0

    elif action == "rea-status":
        rea = probe_rea_adapter()
        print(f"REA Reverse-Engineering Adapter: {rea.status} (Available: {rea.is_available})")
        print(f"  {rea.details}")
        return 0

    else:
        print("Usage: msk-lab research {queue,inspect-static,compare,report,decision,rea-status}")
        return 1



def main():
    parser = argparse.ArgumentParser(description="MSK Research Lab OS v3.0 CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Check environment and runtime prerequisites")
    p_doctor.add_argument("--json", dest="json_output", action="store_true", help="Output JSON only")
    p_doctor.set_defaults(func=cmd_doctor)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start local web dashboard & API")
    p_serve.add_argument("--host", default=None, help="Host interface (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=None, help="Port (default: 8091)")
    p_serve.add_argument("--reload", action="store_true", help="Enable hot reload")
    p_serve.set_defaults(func=cmd_serve)

    # migrate
    p_migrate = subparsers.add_parser("migrate", help="Run database migrations")
    p_migrate.set_defaults(func=cmd_migrate)

    # discovery
    p_discovery = subparsers.add_parser("discovery", help="Discovery pipeline commands (DISC-01, DISC-02)")
    disc_subs = p_discovery.add_subparsers(dest="discovery_action", help="Discovery actions")

    p_disc_import = disc_subs.add_parser("import-md", help="Import local Markdown repository list")
    p_disc_import.add_argument("file", help="Path to markdown file (within research/references)")
    p_disc_import.set_defaults(func=cmd_discovery)

    p_disc_search = disc_subs.add_parser("search-github", help="Search GitHub for biomedical/MSK repos")
    p_disc_search.add_argument("query", help="Keyword search query")
    p_disc_search.add_argument("--topic", default=None, help="Optional topic filter")
    p_disc_search.add_argument("--language", default=None, help="Optional language filter")
    p_disc_search.set_defaults(func=cmd_discovery)

    p_disc_list = disc_subs.add_parser("list", help="List registered discovery candidates")
    p_disc_list.set_defaults(func=cmd_discovery)

    # research
    p_research = subparsers.add_parser("research", help="Research workbench commands (DISC-03, DISC-04, REV-01..02)")
    res_subs = p_research.add_subparsers(dest="research_action", help="Research actions")

    p_res_queue = res_subs.add_parser("queue", help="Enroll candidate into research queue")
    p_res_queue.add_argument("repo_id", help="Candidate ID (e.g. cand_owner_repo)")
    p_res_queue.add_argument("--priority", default="HIGH", choices=["LOW", "MEDIUM", "HIGH", "URGENT"])
    p_res_queue.set_defaults(func=cmd_research)

    p_res_inspect = res_subs.add_parser("inspect-static", help="Perform static AST and code analysis")
    p_res_inspect.add_argument("repo_id", help="Candidate ID")
    p_res_inspect.set_defaults(func=cmd_research)

    p_res_compare = res_subs.add_parser("compare", help="Compare candidates side-by-side")
    p_res_compare.add_argument("repo_ids", nargs="+", help="Two or more candidate IDs")
    p_res_compare.set_defaults(func=cmd_research)

    p_res_report = res_subs.add_parser("report", help="Generate source-cited research report")
    p_res_report.add_argument("repo_id", help="Candidate ID")
    p_res_report.add_argument("--reviewer", default="OPERATOR", help="Reviewer identity")
    p_res_report.set_defaults(func=cmd_research)

    p_res_dec = res_subs.add_parser("decision", help="Record human evaluation decision")
    p_res_dec.add_argument("repo_id", help="Candidate ID")
    p_res_dec.add_argument("--decision", required=True, choices=["ADOPT", "ADAPT", "REJECT", "DEFER"])
    p_res_dec.add_argument("--justification", required=True, help="Detailed justification for decision")
    p_res_dec.add_argument("--reviewer", default="OPERATOR")
    p_res_dec.set_defaults(func=cmd_research)

    p_res_rea = res_subs.add_parser("rea-status", help="Probe optional REA adapter status")
    p_res_rea.set_defaults(func=cmd_research)


    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
