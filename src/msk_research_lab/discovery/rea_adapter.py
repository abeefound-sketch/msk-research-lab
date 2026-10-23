"""Optional Reverse-Engineering Adapter (REV-02).

REA is a separate, optional tool for authorized investigations.
If not installed, reports OPTIONAL_UNAVAILABLE without blocking the Lab OS.
"""

import shutil
import subprocess
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class REAStatus(BaseModel):
    is_available: bool = False
    status: str = "OPTIONAL_UNAVAILABLE"
    cli_path: Optional[str] = None
    version: Optional[str] = None
    details: str = Field(
        default="REA (morluto/rea) is not installed on this host. Optional reverse-engineering workbench is inactive."
    )


def probe_rea_adapter() -> REAStatus:
    """Probe whether the optional REA CLI is installed and consented.

    Never attempts auto-installation.
    """
    rea_path = shutil.which("rea") or shutil.which("rea-agents")
    if not rea_path:
        return REAStatus(
            is_available=False,
            status="OPTIONAL_UNAVAILABLE",
            cli_path=None,
            version=None,
            details="REA (morluto/rea) CLI not found in system PATH. Workbench defaults to safe static AST inspection."
        )

    # Check version safely
    try:
        res = subprocess.run([rea_path, "--version"], capture_output=True, text=True, timeout=5)
        version = res.stdout.strip() or "UNKNOWN"
        return REAStatus(
            is_available=True,
            status="AVAILABLE_PENDING_OPERATOR_CONSENT",
            cli_path=rea_path,
            version=version,
            details=f"REA detected at {rea_path} (version: {version}). Explicit operator consent required per investigation."
        )
    except Exception as e:
        return REAStatus(
            is_available=False,
            status="OPTIONAL_UNAVAILABLE",
            cli_path=rea_path,
            version=None,
            details=f"REA probe error: {str(e)}"
        )
