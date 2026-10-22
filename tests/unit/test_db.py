"""Unit tests for SQLite WAL, foreign keys and transactional migrations."""

import sqlite3
import tempfile
from pathlib import Path
import pytest
from msk_research_lab.core.db import init_connection, get_db, check_db_health
from msk_research_lab.core.migrations import run_migrations


def test_sqlite_wal_and_fk_settings():
    with tempfile.NamedTemporaryFile(suffix=".sqlite3") as tmp:
        path = Path(tmp.name)
        conn = init_connection(path)

        # Check WAL
        cur = conn.execute("PRAGMA journal_mode;")
        assert cur.fetchone()[0].upper() == "WAL"

        # Check Foreign Keys
        cur = conn.execute("PRAGMA foreign_keys;")
        assert cur.fetchone()[0] == 1

        conn.close()


def test_foreign_key_enforcement():
    with tempfile.NamedTemporaryFile(suffix=".sqlite3") as tmp:
        path = Path(tmp.name)
        run_migrations(path)

        with get_db(path) as conn:
            # Attempting to insert an approval referencing non-existent repo must fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO execution_approvals (repo_id, profile_id, commit_sha, approved_by, approval_token)
                    VALUES ('non_existent_repo', 'profile_1', 'abc123', 'admin', 'token_123');
                    """
                )


def test_migration_idempotency():
    with tempfile.NamedTemporaryFile(suffix=".sqlite3") as tmp:
        path = Path(tmp.name)
        applied_first = run_migrations(path)
        assert len(applied_first) >= 1

        applied_second = run_migrations(path)
        assert len(applied_second) == 0  # No duplicate execution

        health = check_db_health(path)
        assert health["connected"] is True
        assert health["wal_mode"] is True
        assert health["fk_enabled"] is True
        assert health["integrity_ok"] is True
        assert health["schema_version"] >= 1
