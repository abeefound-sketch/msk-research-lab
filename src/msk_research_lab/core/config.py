"""Configuration management for MSK Research Lab OS v3.0."""

from pathlib import Path
import os
from typing import Optional
from pydantic import BaseModel, Field

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for Python 3.10


def _find_repo_root() -> Path:
    anchor = Path(__file__).resolve().parent.parent.parent.parent
    if (anchor / "pyproject.toml").exists():
        return anchor
    cwd = Path(os.getcwd()).resolve()
    if (cwd / "pyproject.toml").exists():
        return cwd
    return anchor


def get_desktop_user_data_dir() -> Path:
    """Return standard user data directory for desktop application mode."""
    if os.name == "nt" or "LOCALAPPDATA" in os.environ or "APPDATA" in os.environ:
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return (Path(base) / "MSKResearchLab").resolve()
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return (Path(xdg_data) / "msk_research_lab").resolve()
    return (Path.home() / ".local" / "share" / "msk_research_lab").resolve()


class ServerConfig(BaseModel):
    host: str = Field(default="127.0.0.1", description="Server host, default loopback only")
    port: int = Field(default=8091, description="Server port, default 8091")


class StorageConfig(BaseModel):
    root_dir: Path = Field(default_factory=_find_repo_root)
    data_dir: Path = Field(default=Path("2data"))
    db_path: Path = Field(default=Path("2data/db/lab.sqlite3"))
    docs_dir: Path = Field(default=Path("1docs"))
    refs_dir: Path = Field(default=Path("3refs"))
    incidents_dir: Path = Field(default=Path("4incidents"))
    upstream_dir: Path = Field(default=Path("3refs/upstream"))
    evidence_dir: Path = Field(default=Path("2data/evidence"))


class SecurityConfig(BaseModel):
    default_execution: str = Field(default="deny")
    require_sandbox_enforcement: bool = Field(default=True)
    loopback_only: bool = Field(default=True)
    api_token: Optional[str] = Field(default=None)


class WorkersConfig(BaseModel):
    max_heavy_concurrency: int = Field(default=1)


class AppConfig(BaseModel):
    version: str = "3.0.0"
    release: str = "R0"
    server: ServerConfig = Field(default_factory=ServerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    workers: WorkersConfig = Field(default_factory=WorkersConfig)

    @property
    def data_dir(self) -> Path:
        p = self.storage.data_dir
        if not p.is_absolute():
            return (self.storage.root_dir / p).resolve()
        return p.resolve()

    @property
    def root_dir(self) -> Path:
        return self.storage.root_dir


    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppConfig":
        """Load configuration from TOML file or environment."""
        cfg_dict = {}

        # Look for workspace.toml or config/workspace.toml
        search_paths = []
        if config_path:
            search_paths.append(config_path)
        search_paths.extend([
            Path("config/workspace.toml"),
            Path("workspace.toml"),
            Path("config/workspace.example.toml")
        ])

        for p in search_paths:
            if p.exists():
                try:
                    with open(p, "rb") as f:
                        cfg_dict = tomllib.load(f)
                    break
                except Exception:
                    pass

        # Environment variable overrides
        server_dict = cfg_dict.get("server", {})
        if "MSK_LAB_HOST" in os.environ:
            server_dict["host"] = os.environ["MSK_LAB_HOST"]
        if "MSK_LAB_PORT" in os.environ:
            server_dict["port"] = int(os.environ["MSK_LAB_PORT"])

        storage_dict = cfg_dict.get("storage", {})
        storage_mode = os.environ.get("MSK_STORAGE_MODE", "").lower()
        if storage_mode in ("desktop", "appdata", "user"):
            desktop_dir = get_desktop_user_data_dir()
            desktop_dir.mkdir(parents=True, exist_ok=True)
            storage_dict["data_dir"] = desktop_dir
            storage_dict["db_path"] = desktop_dir / "db" / "lab.sqlite3"
            storage_dict["evidence_dir"] = desktop_dir / "evidence"

        if "MSK_LAB_DATA_DIR" in os.environ:
            storage_dict["data_dir"] = Path(os.environ["MSK_LAB_DATA_DIR"])
        if "MSK_LAB_DB_PATH" in os.environ:
            storage_dict["db_path"] = Path(os.environ["MSK_LAB_DB_PATH"])

        security_dict = cfg_dict.get("security", {})
        if "MSK_LAB_API_KEY" in os.environ:
            security_dict["api_token"] = os.environ["MSK_LAB_API_KEY"]

        return cls(
            server=ServerConfig(**server_dict),
            storage=StorageConfig(**storage_dict),
            security=SecurityConfig(**security_dict),
            workers=WorkersConfig(**cfg_dict.get("workers", {}))
        )


_config: Optional[AppConfig] = None


def get_config(reload: bool = False) -> AppConfig:
    global _config
    if _config is None or reload:
        _config = AppConfig.load()
    return _config
