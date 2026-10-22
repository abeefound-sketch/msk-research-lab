"""Transactional migration runner for MSK Research Lab OS SQLite database."""

import datetime
from pathlib import Path
from typing import List, Tuple, Optional
from msk_research_lab.core.db import get_db

MIGRATIONS: List[Tuple[int, str, str]] = [
    (
        1,
        "0001_initial_r0_baseline",
        """
        -- Audit Events Ledger
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'LOGGED',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- System State Key-Value Table
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- Repositories (Metadata & Inspection Registry)
        CREATE TABLE IF NOT EXISTS repositories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            upstream_url TEXT NOT NULL,
            license TEXT NOT NULL DEFAULT 'UNKNOWN',
            status TEXT NOT NULL DEFAULT 'REGISTERED_UNINSPECTED',
            target_kind TEXT NOT NULL DEFAULT 'GENERAL_RESEARCH',
            pinned_commit_sha TEXT,
            catalog_metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- Repository Run Profiles (Explicit, disabled-by-default execution profiles)
        CREATE TABLE IF NOT EXISTS repo_run_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            sandbox_type TEXT NOT NULL DEFAULT 'SUBPROCESS_ISOLATED',
            max_memory_mb INTEGER NOT NULL DEFAULT 512,
            max_cpu_percent INTEGER NOT NULL DEFAULT 50,
            timeout_seconds INTEGER NOT NULL DEFAULT 300,
            allowed_ports_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'DISABLED',
            is_approved INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- Explicit Human Approvals
        CREATE TABLE IF NOT EXISTS execution_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            approved_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            approval_token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            FOREIGN KEY(repo_id) REFERENCES repositories(id) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_repos_status ON repositories(status);
        CREATE INDEX IF NOT EXISTS idx_approvals_repo ON execution_approvals(repo_id);
        """
    )
]


def init_migration_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );
    """)


def get_applied_migrations(conn) -> List[int]:
    init_migration_table(conn)
    cur = conn.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
    return [row[0] for row in cur.fetchall()]


def run_migrations(custom_path: Optional[Path] = None) -> List[str]:
    """Run pending migrations in sequence within individual transactions."""
    applied_names = []
    with get_db(custom_path) as conn:
        init_migration_table(conn)
        applied = set(get_applied_migrations(conn))

        for version, name, sql in MIGRATIONS:
            if version not in applied:
                # Execute migration within transaction
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?);",
                    (version, name, datetime.datetime.utcnow().isoformat() + "Z")
                )
                # Record audit event
                conn.execute(
                    "INSERT INTO audit_events (event_type, actor, payload_json) VALUES (?, ?, ?);",
                    ("MIGRATION_APPLIED", "SYSTEM", f'{{"version": {version}, "name": "{name}"}}')
                )
                applied_names.append(name)

    return applied_names
