"""Unit tests for research notes, multi-source citations, and JSON export."""

import pytest
import tempfile
from pathlib import Path
from tests.fixtures.synthetic_docs import generate_synthetic_fixtures
from msk_research_lab.library.store import store_original_document
from msk_research_lab.library.parsers import parse_and_index_document
from msk_research_lab.research.notes import create_research_note, get_research_note, export_note_to_json, CitationError
from msk_research_lab.core.migrations import run_migrations


def test_create_note_with_g5_required_citations():
    """G5 requirement: At least 2 document citations + 1 Git commit SHA."""
    run_migrations()
    with tempfile.TemporaryDirectory() as tmp:
        fixtures = generate_synthetic_fixtures(Path(tmp))

        # Ingest two documents
        doc1 = store_original_document(fixtures["epub"][0])
        doc2 = store_original_document(fixtures["docx"][0])

        locs1 = parse_and_index_document(doc1["document_id"], Path(doc1["storage_path"]), "EPUB")
        locs2 = parse_and_index_document(doc2["document_id"], Path(doc2["storage_path"]), "DOCX")

        citations = [
            {
                "target_kind": "DOCUMENT_LOCATION",
                "document_id": doc1["document_id"],
                "location_id": locs1[0]["id"],
                "comment": "Primary clinical finding"
            },
            {
                "target_kind": "DOCUMENT_LOCATION",
                "document_id": doc2["document_id"],
                "location_id": locs2[0]["id"],
                "comment": "Corroborating palpation finding"
            },
            {
                "target_kind": "GIT_COMMIT",
                "git_repo_id": "jicio--tcm-3d",
                "git_commit_sha": "a1b2c3d4e5f678901234567890abcdef12345678",
                "excerpt": "Surface anchoring implementation",
                "comment": "Reproduced on commit a1b2c3d4"
            }
        ]

        note = create_research_note(
            title="Comparison of Trapezius Palpation across Sources",
            content_markdown="Observed strong alignment on scapular spine reference point.",
            citations=citations
        )

        assert note["title"] == "Comparison of Trapezius Palpation across Sources"
        assert len(note["citations"]) == 3

        # Test JSON export
        export_data = export_note_to_json(note["id"])
        assert export_data["export_kind"] == "RESEARCH_NOTE"
        assert len(export_data["note"]["citations"]) == 3


def test_reject_unresolved_citation():
    run_migrations()
    with pytest.raises(CitationError):
        create_research_note(
            title="Invalid Note",
            content_markdown="Should fail",
            citations=[{
                "target_kind": "DOCUMENT_LOCATION",
                "document_id": "non-existent-doc",
                "location_id": "non-existent-loc"
            }]
        )
