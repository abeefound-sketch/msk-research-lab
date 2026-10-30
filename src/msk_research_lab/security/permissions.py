"""Filesystem permissions security helper for Windows NTFS and POSIX."""

import getpass
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def get_current_windows_identity() -> Optional[str]:
    """Resolve the current execution identity on Windows with multi-tier fallback (DEF-31).
    
    1. USERNAME / USER environment variables.
    2. getpass.getuser() standard library resolution.
    3. Win32 Advapi32 GetUserNameW via ctypes.
    4. Fallback to standard Owner Rights SID '*S-1-3-4'.
    """
    # 1. Environment variables
    env_user = os.environ.get("USERNAME") or os.environ.get("USER")
    if env_user and env_user.strip():
        return env_user.strip()

    # 2. getpass
    try:
        gp_user = getpass.getuser()
        if gp_user and gp_user.strip():
            return gp_user.strip()
    except Exception:
        pass

    # 3. Win32 Advapi32 GetUserNameW
    if sys.platform == "win32":
        try:
            import ctypes
            buffer = ctypes.create_unicode_buffer(256)
            size = ctypes.c_ulong(256)
            if ctypes.windll.advapi32.GetUserNameW(buffer, ctypes.byref(size)):
                if buffer.value and buffer.value.strip():
                    return buffer.value.strip()
        except Exception:
            pass

    # 4. Standard Owner Rights SID fallback
    return "*S-1-3-4"


def secure_file_permissions(path: Path) -> None:
    """Enforce restrictive permissions on sensitive key or database files (DEF-22, DEF-31).
    
    POSIX: 0o600 (read/write only by owner).
    Windows NTFS: icacls /inheritance:r /grant:r "<identity>":F (removes inherited DACLs).
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
            identity = get_current_windows_identity()
            if identity:
                subprocess.run(
                    ["icacls", str(path_obj), "/inheritance:r", "/grant:r", f"{identity}:F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass


def secure_directory_permissions(path: Path) -> None:
    """Enforce restrictive permissions on sensitive directory structures (DEF-22, DEF-31).
    
    POSIX: 0o700 (read/write/search only by owner).
    Windows NTFS: icacls /inheritance:r /grant:r "<identity>":(OI)(CI)F.
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
            identity = get_current_windows_identity()
            if identity:
                subprocess.run(
                    ["icacls", str(path_obj), "/inheritance:r", "/grant:r", f"{identity}:(OI)(CI)F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

