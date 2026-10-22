"""Unit tests for configuration loading."""

from pathlib import Path
from msk_research_lab.core.config import AppConfig, get_config


def test_default_config():
    cfg = AppConfig.load()
    assert cfg.version == "3.0.0"
    assert cfg.release == "R0"
    assert cfg.server.host == "127.0.0.1"
    assert cfg.server.port == 8091
    assert cfg.security.loopback_only is True
    assert cfg.security.default_execution == "deny"
    assert cfg.security.require_sandbox_enforcement is True
    assert cfg.workers.max_heavy_concurrency == 1


def test_storage_paths():
    cfg = get_config()
    assert cfg.storage.data_dir == Path("2data")
    assert cfg.storage.docs_dir == Path("1docs")
    assert cfg.storage.refs_dir == Path("3refs")
    assert cfg.storage.incidents_dir == Path("4incidents")
