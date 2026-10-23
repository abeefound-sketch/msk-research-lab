"""Unit tests for document parsers (PDF, EPUB, DOCX) and locator extraction."""

import tempfile
from pathlib import Path
from tests.fixtures.synthetic_docs import generate_synthetic_fixtures
from msk_research_lab.library.store import store_original_document
from msk_research_lab.library.parsers import parse_and_index_document
from msk_research_lab.core.migrations import run_migrations


def test_parse_10_synthetic_fixtures():
    run_migrations()
    with tempfile.TemporaryDirectory() as tmp:
        fixtures = generate_synthetic_fixtures(Path(tmp))
        assert len(fixtures["pdf"]) == 4
        assert len(fixtures["epub"]) == 3
        assert len(fixtures["docx"]) == 3

        # 1. Parse 4 PDFs
        for p in fixtures["pdf"]:
            doc = store_original_document(p)
            locs = parse_and_index_document(doc["document_id"], Path(doc["storage_path"]), "PDF")
            assert len(locs) >= 1
            for loc in locs:
                assert loc["location_type"] == "PDF_PAGE"
                assert loc["page_number"] >= 1  # Strictly 1-based

        # 2. Parse 3 EPUBs
        for e in fixtures["epub"]:
            doc = store_original_document(e)
            locs = parse_and_index_document(doc["document_id"], Path(doc["storage_path"]), "EPUB")
            assert len(locs) >= 1
            for loc in locs:
                assert loc["location_type"] == "EPUB_CHAPTER"
                assert loc["spine_href"] is not None

        # 3. Parse 3 DOCXs
        for d in fixtures["docx"]:
            doc = store_original_document(d)
            locs = parse_and_index_document(doc["document_id"], Path(doc["storage_path"]), "DOCX")
            assert len(locs) >= 1
            types = {l["location_type"] for l in locs}
            assert "DOCX_PARAGRAPH" in types
            assert "DOCX_TABLE" in types
