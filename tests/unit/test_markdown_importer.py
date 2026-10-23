"""Unit tests for DISC-01 local Markdown importer and provenance tracking."""

import pytest
import tempfile
from pathlib import Path
from msk_research_lab.core.db import get_db
from msk_research_lab.core.migrations import run_migrations
from msk_research_lab.discovery.markdown_importer import (
    import_markdown_reference_list,
    validate_import_path,
    ImportSecurityError,
    MAX_FILE_SIZE_BYTES
)


@pytest.fixture
def clean_db(tmp_path):
    db_file = tmp_path / "test_discovery.sqlite3"
    run_migrations(db_file)
    return db_file


def test_import_markdown_positive(tmp_path, clean_db):
    allowlist_dir = tmp_path / "refs"
    allowlist_dir.mkdir()
    md_file = allowlist_dir / "awesome_msk_repos.md"

    md_content = """# Curated MSK Repositories

| Repository | Purpose | License |
|---|---|---|
| [Open Anatomy](https://github.com/openanatomy/open-anatomy-browser?utm_source=news) | WebGL Atlas | Slicer |

Here is another tool:
Check [TCM 3D](https://github.com/JICio/tcm-3d) for 3D reflexology points.

Direct link without markdown link syntax:
https://github.com/WaterCMY/anatomy-3d

And a repeated reference to the first repo on line 13:
Reference to [Open Anatomy Browser](https://github.com/openanatomy/open-anatomy-browser#readme) in notes.

```bash
# Code block should be ignored
git clone https://github.com/fake-owner/fake-repo
```
"""
    md_file.write_text(md_content, encoding="utf-8")

    summary = import_markdown_reference_list(
        file_path=md_file,
        allowlist_dir=allowlist_dir,
        custom_db_path=clean_db
    )

    # 3 unique candidates, 4 occurrences
    assert summary.candidate_count == 3
    assert summary.occurrence_count == 4
    assert summary.new_candidates_registered == 3
    assert len(summary.skipped_invalid_urls) == 0

    with get_db(clean_db) as conn:
        # Check reference_documents
        doc = conn.execute("SELECT * FROM reference_documents WHERE id = ?", (summary.document_id,)).fetchone()
        assert doc is not None
        assert doc["candidate_count"] == 3

        # Check repository_candidates
        cands = conn.execute("SELECT id, canonical_url, status, discovery_source FROM repository_candidates ORDER BY id").fetchall()
        assert len(cands) == 3
        urls = [c["canonical_url"] for c in cands]
        assert "https://github.com/openanatomy/open-anatomy-browser" in urls
        assert "https://github.com/JICio/tcm-3d" in urls
        assert "https://github.com/WaterCMY/anatomy-3d" in urls

        # All must be DISCOVERED_UNVERIFIED
        for c in cands:
            assert c["status"] == "DISCOVERED_UNVERIFIED"
            assert c["discovery_source"] == "MARKDOWN_IMPORT"

        # Check occurrences
        occs = conn.execute("SELECT * FROM reference_occurrences WHERE document_id = ? ORDER BY line_number", (summary.document_id,)).fetchall()
        assert len(occs) == 4
        assert occs[0]["line_number"] == 5
        assert occs[0]["link_label"] == "Open Anatomy"
        assert occs[1]["line_number"] == 8
        assert occs[1]["link_label"] == "TCM 3D"
        assert occs[2]["line_number"] == 11
        assert occs[2]["link_label"] is None
        assert occs[3]["line_number"] == 14
        assert occs[3]["link_label"] == "Open Anatomy Browser"


def test_import_markdown_path_traversal_rejected(tmp_path, clean_db):
    allowlist_dir = tmp_path / "refs"
    allowlist_dir.mkdir()

    outside_file = tmp_path / "outside.md"
    outside_file.write_text("# Outside list\nhttps://github.com/test/repo", encoding="utf-8")

    with pytest.raises(ImportSecurityError) as exc_info:
        import_markdown_reference_list(
            file_path=outside_file,
            allowlist_dir=allowlist_dir,
            custom_db_path=clean_db
        )
    assert "outside allowlisted directory" in str(exc_info.value)


def test_import_markdown_disallowed_extension(tmp_path, clean_db):
    allowlist_dir = tmp_path / "refs"
    allowlist_dir.mkdir()

    script_file = allowlist_dir / "exploit.sh"
    script_file.write_text("#!/bin/bash\nhttps://github.com/test/repo", encoding="utf-8")

    with pytest.raises(ImportSecurityError) as exc_info:
        import_markdown_reference_list(
            file_path=script_file,
            allowlist_dir=allowlist_dir,
            custom_db_path=clean_db
        )
    assert "Disallowed extension" in str(exc_info.value)


def test_import_markdown_malformed_url_skipped(tmp_path, clean_db):
    allowlist_dir = tmp_path / "refs"
    allowlist_dir.mkdir()
    md_file = allowlist_dir / "mixed_urls.md"

    md_content = """# Repos
1. Good: [Valid Repo](https://github.com/owner/valid-repo)
2. Deceptive: [Fake](https://github.com.attacker.com/evil/repo)
3. Credentials: [Creds](https://user:pass@github.com/leak/repo)
"""
    md_file.write_text(md_content, encoding="utf-8")

    summary = import_markdown_reference_list(
        file_path=md_file,
        allowlist_dir=allowlist_dir,
        custom_db_path=clean_db
    )

    assert summary.candidate_count == 1
    assert len(summary.skipped_invalid_urls) == 2
    reasons = [item["reason"] for item in summary.skipped_invalid_urls]
    assert any("lookalike" in r for r in reasons)
    assert any("credentials" in r for r in reasons)
