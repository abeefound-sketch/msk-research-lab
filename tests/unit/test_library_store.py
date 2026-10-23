"""Unit tests for document store, format detection and safety limits."""

import pytest
import tempfile
from pathlib import Path
from msk_research_lab.library.store import (
    store_original_document,
    detect_file_type,
    compute_sha256,
    DocumentSecurityError
)
from msk_research_lab.core.migrations import run_migrations


def test_detect_file_type():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        pdf = d / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 sample pdf content")
        assert detect_file_type(pdf) == "PDF"

        txt = d / "malicious.sh"
        txt.write_bytes(b"#!/bin/bash\necho bad")
        assert detect_file_type(txt) == "UNKNOWN"


def test_reject_unsupported_format():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        bad_file = d / "malicious.exe"
        bad_file.write_bytes(b"MZ\x90\x00\x03")
        with pytest.raises(DocumentSecurityError):
            store_original_document(bad_file)


def test_store_and_deduplicate_document():
    run_migrations()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        pdf = d / "sample.pdf"
        pdf.write_bytes(b"%PDF-1.5 test document bytes")

        res1 = store_original_document(pdf)
        assert res1["file_type"] == "PDF"
        assert len(res1["sha256"]) == 64
        assert Path(res1["storage_path"]).exists()

        # Ingesting same file again should yield same hash and document_id
        res2 = store_original_document(pdf)
        assert res2["sha256"] == res1["sha256"]
        assert res2["document_id"] == res1["document_id"]
