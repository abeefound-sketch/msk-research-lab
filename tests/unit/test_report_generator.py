"""Unit tests for DISC-04 candidate comparison, report generation, and REA probing."""

import pytest
import json
import hashlib
from pathlib import Path
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.discovery.report_generator import compare_candidates, generate_research_report
from msk_research_lab.discovery.rea_adapter import probe_rea_adapter


@pytest.fixture
def clean_db(tmp_path):
    db_file = tmp_path / "test_reports.sqlite3"
    run_migrations(db_file)

    # Seed 2 candidates
    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO repository_candidates (
                id, canonical_url, owner, repo, status, priority,
                primary_language, license_spdx, discovery_source
            ) VALUES
            ('cand_oab', 'https://github.com/openanatomy/open-anatomy-browser', 'openanatomy', 'open-anatomy-browser', 'STATIC_ANALYZED', 'HIGH', 'TypeScript', 'BSD-3-Clause', 'MARKDOWN_IMPORT'),
            ('cand_tcm', 'https://github.com/JICio/tcm-3d', 'JICio', 'tcm-3d', 'BLOCKED', 'MEDIUM', 'JavaScript', 'MIT', 'MARKDOWN_IMPORT');
            """
        )

        # Seed static analysis artifact for cand_oab
        conn.execute(
            """
            INSERT INTO static_analysis_artifacts (
                id, candidate_id, commit_sha, languages_json, entrypoints_json,
                dependencies_json, risk_hooks_json, ui_framework, model_formats_json
            ) VALUES (
                'art_oab_01', 'cand_oab', 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
                '{"TypeScript": 50}', '[{"type": "NPM_MAIN", "file": "dist/index.js", "line": 1}]',
                '[{"ecosystem": "npm", "name": "three", "version": "0.150.0"}]',
                '[]', 'Three.js / WebGL 3D', '[\".glb\", \".obj\"]'
            );
            """
        )

        # Seed reference document and occurrence
        conn.execute(
            """
            INSERT INTO reference_documents (id, file_path, file_sha256, line_count, candidate_count)
            VALUES ('doc_sample', '/path/to/awesome.md', 'dummyhash123', 20, 2);
            """
        )
        conn.execute(
            """
            INSERT INTO reference_occurrences (document_id, candidate_id, line_number, raw_url, link_label, context_snippet)
            VALUES ('doc_sample', 'cand_oab', 7, 'https://github.com/openanatomy/open-anatomy-browser', 'Open Anatomy Browser', 'Check out Open Anatomy Browser');
            """
        )

        # Seed research decision
        conn.execute(
            """
            INSERT INTO research_decisions (candidate_id, decision, justification, reviewed_by)
            VALUES ('cand_oab', 'ADAPT', 'Can adapt the WebGL coordinate loader for MSK anatomical points.', 'LEAD_DEV');
            """
        )

    return db_file


def test_compare_candidates(clean_db):
    comp = compare_candidates(["cand_oab", "cand_tcm"], custom_db_path=clean_db)

    assert comp["compared_candidates_count"] == 2
    matrix = comp["comparison_matrix"]
    assert matrix["licenses"]["cand_oab"] == "BSD-3-Clause"
    assert matrix["licenses"]["cand_tcm"] == "MIT"
    assert matrix["ui_frameworks"]["cand_oab"] == "Three.js / WebGL 3D"
    assert matrix["hardware_readiness"]["cand_tcm"] == "SANDBOX_BLOCKED"


def test_compare_candidates_minimum_count(clean_db):
    with pytest.raises(ValueError):
        compare_candidates(["cand_oab"], custom_db_path=clean_db)


def test_generate_research_report(clean_db, tmp_path):
    reports_dir = tmp_path / "reports"
    res = generate_research_report(
        candidate_id="cand_oab",
        reviewer="LEAD_DEV",
        custom_db_path=clean_db,
        output_base_dir=reports_dir
    )

    assert res["candidate_id"] == "cand_oab"
    assert res["decision"] == "ADAPT"
    assert res["revision"] == 1

    report_dir = Path(res["report_dir"])
    assert report_dir.exists()
    assert (report_dir / "report.md").exists()
    assert (report_dir / "report.json").exists()
    assert (report_dir / "manifest.sha256").exists()

    md_text = (report_dir / "report.md").read_text(encoding="utf-8")
    assert "# Scholarly Research Report: openanatomy/open-anatomy-browser" in md_text
    assert "Three.js / WebGL 3D" in md_text
    assert "awesome.md" in md_text
    assert "UNREVIEWED_SOURCE_FINDING" in md_text

    # Verify manifest integrity
    manifest_lines = (report_dir / "manifest.sha256").read_text(encoding="utf-8").splitlines()
    assert len(manifest_lines) == 2

    # Verify Tri-Ledger ingestion
    with get_db(clean_db) as conn:
        evi = conn.execute("SELECT * FROM evidence WHERE evidence_id = ?", (res["tri_ledger_evidence_id"],)).fetchone()
        assert evi is not None
        assert evi["review_state"] == "UNREVIEWED"
        assert evi["source_kind"] == "COMPUTATIONAL_OBSERVATION"


def test_probe_rea_adapter():
    status = probe_rea_adapter()
    # On this host where REA is not installed, it should report OPTIONAL_UNAVAILABLE cleanly
    if not status.is_available:
        assert status.status == "OPTIONAL_UNAVAILABLE"
        assert "not found" in status.details or "not installed" in status.details
