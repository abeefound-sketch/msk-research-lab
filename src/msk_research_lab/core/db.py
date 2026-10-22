"""SQLite database connection and session management."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from msk_research_lab.core.config import get_config


def get_db_path(custom_path: Optional[Path] = None) -> Path:
    if custom_path:
        return custom_path
    cfg = get_config()
    db_path = cfg.storage.db_path
    if not db_path.is_absolute():
        db_path = cfg.storage.root_dir / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_connection(db_path: Path) -> sqlite3.Connection:
    """Initialize connection with WAL mode, foreign keys, and sensible timeouts."""
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


@contextmanager
def get_db(custom_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections with automatic commit/rollback."""
    path = get_db_path(custom_path)
    conn = init_connection(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_db_health(custom_path: Optional[Path] = None) -> dict:
    """Inspect database connectivity, WAL mode, foreign keys and integrity."""
    path = get_db_path(custom_path)
    if not path.exists():
        return {
            "connected": False,
            "exists": False,
            "wal_mode": False,
            "fk_enabled": False,
            "integrity_ok": False,
            "schema_version": 0,
            "path": str(path)
        }

    try:
        with get_db(path) as conn:
            wal = conn.execute("PRAGMA journal_mode;").fetchone()[0].upper() == "WAL"
            fk = bool(conn.execute("PRAGMA foreign_keys;").fetchone()[0])
            integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0] == "ok"

            # Check migrations table
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';")
            if cur.fetchone():
                v_cur = conn.execute("SELECT MAX(version) FROM schema_migrations;")
                row = v_cur.fetchone()
                version = row[0] if row and row[0] is not None else 0
            else:
                version = 0

            return {
                "connected": True,
                "exists": True,
                "wal_mode": wal,
                "fk_enabled": fk,
                "integrity_ok": integrity,
                "schema_version": version,
                "path": str(path)
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "wal_mode": False,
            "fk_enabled": False,
            "integrity_ok": False,
            "schema_version": 0,
            "path": str(path)
        }
