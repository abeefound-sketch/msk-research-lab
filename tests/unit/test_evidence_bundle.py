"""Unit tests for evidence bundle creation and tamper detection."""

import tempfile
from pathlib import Path
from msk_research_lab.core.evidence import EvidenceBundle, verify_evidence_bundle
from msk_research_lab.core.migrations import run_migrations


def test_evidence_bundle_creation_and_tamper_detection():
    run_migrations()
    bundle = EvidenceBundle(release_id="R1_TEST", run_id="test-run-001")
    bundle.record_json("source", {"repo": "test", "sha": "12345"})
    bundle.record_text("stdout.log", "Sample execution log output\n")

    seal = bundle.finalize()
    assert seal["artifact_count"] == 2
    assert "manifest_hash" in seal

    # 1. Verification of pristine bundle must PASS
    v_clean = verify_evidence_bundle(Path(seal["bundle_dir"]))
    assert v_clean["valid"] is True
    assert len(v_clean["mismatches"]) == 0

    # 2. Tamper with one file -> Verification must FAIL with TAMPER_DETECTED
    stdout_file = Path(seal["bundle_dir"]) / "stdout.log"
    stdout_file.write_text("TAMPERED CONTENT\n", encoding="utf-8")

    v_tampered = verify_evidence_bundle(Path(seal["bundle_dir"]))
    assert v_tampered["valid"] is False
    assert len(v_tampered["mismatches"]) == 1
    assert v_tampered["mismatches"][0]["error"] == "TAMPER_DETECTED"
