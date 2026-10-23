"""Unit tests for disaster recovery backup and restore (G6 requirement)."""

import tempfile
from pathlib import Path
from tests.fixtures.synthetic_docs import generate_synthetic_fixtures
from msk_research_lab.library.store import store_original_document
from msk_research_lab.library.parsers import parse_and_index_document
from msk_research_lab.core.backup import create_backup, restore_backup
from msk_research_lab.core.migrations import run_migrations


def test_backup_and_restore_to_fresh_directory():
    """G6: Backup SQLite and originals; restore to fresh directory; verify hashes & search."""
    run_migrations()
    with tempfile.TemporaryDirectory() as tmp_src:
        fixtures = generate_synthetic_fixtures(Path(tmp_src))
        doc = store_original_document(fixtures["docx"][0])
        parse_and_index_document(doc["document_id"], Path(doc["storage_path"]), "DOCX")

        with tempfile.TemporaryDirectory() as tmp_export, tempfile.TemporaryDirectory() as tmp_restore:
            backup_res = create_backup(Path(tmp_export))
            assert Path(backup_res["archive_path"]).exists()
            assert backup_res["file_count"] >= 1

            restore_res = restore_backup(Path(backup_res["archive_path"]), Path(tmp_restore))
            assert restore_res["status"] == "RESTORE_VERIFIED"
            assert restore_res["sqlite_integrity_ok"] is True
            assert restore_res["fts5_functional"] is True
            assert restore_res["verified_file_count"] == backup_res["file_count"]
