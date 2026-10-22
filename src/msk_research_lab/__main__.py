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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
