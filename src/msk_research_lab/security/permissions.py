"""Filesystem permissions security helper for Windows NTFS and POSIX."""

import os
import subprocess
import sys
from pathlib import Path


def secure_file_permissions(path: Path) -> None:
    """Enforce restrictive permissions on sensitive key or database files (DEF-22).
    
    POSIX: 0o600 (read/write only by owner).
    Windows NTFS: icacls /inheritance:r /grant:r "%USERNAME%":F (removes inherited DACLs).
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return

    # POSIX permissions
    try:
        os.chmod(path_obj, 0o600)
    except Exception:
        pass

    # Windows NTFS permissions
    if sys.platform == "win32":
        try:
            username = os.environ.get("USERNAME") or os.environ.get("USER")
            if username:
                subprocess.run(
                    ["icacls", str(path_obj), "/inheritance:r", "/grant:r", f"{username}:F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass


def secure_directory_permissions(path: Path) -> None:
    """Enforce restrictive permissions on sensitive directory structures (DEF-22).
    
    POSIX: 0o700 (read/write/search only by owner).
    Windows NTFS: icacls /inheritance:r /grant:r "%USERNAME%":(OI)(CI)F.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return

    # POSIX permissions
    try:
        os.chmod(path_obj, 0o700)
    except Exception:
        pass

    # Windows NTFS permissions
    if sys.platform == "win32":
        try:
            username = os.environ.get("USERNAME") or os.environ.get("USER")
            if username:
                subprocess.run(
                    ["icacls", str(path_obj), "/inheritance:r", "/grant:r", f"{username}:(OI)(CI)F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass
