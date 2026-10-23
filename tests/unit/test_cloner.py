"""Unit tests for repository cloner safety and dirty checkout protection."""

import pytest
import tempfile
from pathlib import Path
from msk_research_lab.repos.cloner import get_upstream_repo_dir, CloneSecurityError, is_repo_dirty


def test_safe_upstream_path_resolution():
    p = get_upstream_repo_dir("valid-repo")
    assert "3refs/upstream/valid-repo" in str(p)


def test_reject_upstream_path_traversal():
    with pytest.raises(CloneSecurityError):
        get_upstream_repo_dir("../../etc/shadow")


def test_is_repo_dirty_on_non_git():
    with tempfile.TemporaryDirectory() as tmp_dir:
        assert is_repo_dirty(Path(tmp_dir)) is False
