"""Unit tests for REV-01 static source code analysis and risk detection."""

import pytest
import json
from pathlib import Path
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.discovery.static_analyzer import analyze_repository_static


@pytest.fixture
def clean_db(tmp_path):
    db_file = tmp_path / "test_static.sqlite3"
    run_migrations(db_file)
    with get_db(db_file) as conn:
        conn.execute(
            """
            INSERT INTO repository_candidates (
                id, canonical_url, owner, repo, status, priority, discovery_source
            ) VALUES (
                'cand_mock_repo', 'https://github.com/mock-owner/mock-repo',
                'mock-owner', 'mock-repo', 'RESEARCH_QUEUED', 'HIGH', 'MARKDOWN_IMPORT'
            )
            """
        )
    return db_file


def test_static_analysis_full(tmp_path, clean_db):
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()

    # 1. package.json with entrypoint, Three.js dependency, and postinstall hook
    pkg_json = repo_dir / "package.json"
    pkg_json.write_text(json.dumps({
        "name": "mock-3d-viewer",
        "main": "dist/index.js",
        "scripts": {
            "build": "vite build",
            "postinstall": "node scripts/install-native.js"
        },
        "dependencies": {
            "three": "^0.160.0"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }), encoding="utf-8")

    # 2. Python backend entrypoint with __name__ == '__main__' and os.system
    py_file = repo_dir / "app.py"
    py_file.write_text("""import os
import sys

def run():
    print("Starting server")
    os.system("echo risk")

if __name__ == "__main__":
    run()
""", encoding="utf-8")

    # 3. 3D Model file
    models_dir = repo_dir / "models"
    models_dir.mkdir()
    (models_dir / "torso_mesh.glb").write_bytes(b"GLTF...")

    # 4. Test file
    tests_dir = repo_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_viewer.py").write_text("def test_dummy(): pass\n", encoding="utf-8")

    # Run static analysis
    report = analyze_repository_static(
        repo_dir=repo_dir,
        candidate_id="cand_mock_repo",
        custom_db_path=clean_db
    )

    # Invariants verification
    assert report.candidate_id == "cand_mock_repo"
    assert "Three.js" in report.ui_framework
    assert ".glb" in report.model_formats
    assert report.test_files_count == 1
    assert report.total_files_scanned >= 4

    # Check risk hooks: postinstall npm hook and os.system python call
    hook_names = [h.get("hook") for h in report.risk_hooks]
    assert "postinstall" in hook_names
    assert "OS_SYSTEM_CALL" in hook_names

    # Check entrypoints
    entry_types = [e.get("type") for e in report.entrypoints]
    assert "NPM_MAIN" in entry_types
    assert "PYTHON_MAIN_BLOCK" in entry_types

    # Check database persistence
    with get_db(clean_db) as conn:
        cand = conn.execute("SELECT status FROM repository_candidates WHERE id = 'cand_mock_repo'").fetchone()
        assert cand["status"] == "STATIC_ANALYZED"

        artifact = conn.execute("SELECT * FROM static_analysis_artifacts WHERE candidate_id = 'cand_mock_repo'").fetchone()
        assert artifact is not None
        assert "three" in artifact["dependencies_json"]
        assert "postinstall" in artifact["risk_hooks_json"]
