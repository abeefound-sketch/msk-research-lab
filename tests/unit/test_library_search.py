"""Unit tests for FTS5 full-text search and location resolution."""

import tempfile
from pathlib import Path
from tests.fixtures.synthetic_docs import generate_synthetic_fixtures
from msk_research_lab.library.store import store_original_document
from msk_research_lab.library.parsers import parse_and_index_document
from msk_research_lab.library.search import search_library, resolve_location
from msk_research_lab.core.migrations import run_migrations


def test_fts5_search_and_location_resolution():
    run_migrations()
    with tempfile.TemporaryDirectory() as tmp:
        fixtures = generate_synthetic_fixtures(Path(tmp))

        # Ingest and index one EPUB and one DOCX
        epub_res = store_original_document(fixtures["epub"][0])
        docx_res = store_original_document(fixtures["docx"][0])

        epub_locs = parse_and_index_document(epub_res["document_id"], Path(epub_res["storage_path"]), "EPUB")
        docx_locs = parse_and_index_document(docx_res["document_id"], Path(docx_res["storage_path"]), "DOCX")

        # 1. Search for keyword in EPUB: "trapezius"
        hits_epub = search_library("trapezius")
        assert len(hits_epub) >= 1
        assert "trapezius" in hits_epub[0]["snippet"].lower()
        assert hits_epub[0]["location_type"] == "EPUB_CHAPTER"

        # 2. Search for keyword in DOCX: "scapula"
        hits_docx = search_library("scapula")
        assert len(hits_docx) >= 1
        assert "scapula" in hits_docx[0]["snippet"].lower()

        # 3. Resolve exact location
        resolved = resolve_location(epub_res["document_id"], epub_locs[0]["id"])
        assert resolved["status"] == "RESOLVED"
        assert resolved["location_type"] == "EPUB_CHAPTER"
        assert len(resolved["text_content"]) > 0

        # 4. Unknown location yields UNRESOLVED
        unres = resolve_location(epub_res["document_id"], "non-existent-loc-id")
        assert unres["status"] == "UNRESOLVED"
