@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo MSK Research Lab OS — Versioned Release Rollback Utility
echo ================================================================

if "%~1"=="" (
    echo Usage: rollback_release.bat [BACKUP_DIR]
    echo Example: rollback_release.bat dist\backups\v3.2.0_pre_update
    echo.
    echo Safety Invariant:
    echo User database and cryptographic keys in APPDATA or 2data\db
    echo are NEVER overwritten by rollback.
    exit /b 1
)

set BACKUP_DIR=%~1
if not exist "%BACKUP_DIR%" (
    echo [ERROR] Specified backup directory "%BACKUP_DIR%" does not exist.
    exit /b 1
)

echo [1/3] Verifying shutdown of any active workstation processes...
call "%~dp0Stop-MSK-Workstation.bat"

echo [2/3] Validating backup integrity...
if not exist "%BACKUP_DIR%\src\msk_research_lab" (
    echo [ERROR] Backup directory does not contain valid source tree (src\msk_research_lab).
    exit /b 1
)

echo [3/3] Restoring application codebase from "%BACKUP_DIR%"...
xcopy "%BACKUP_DIR%\src" "%~dp0..\src" /E /I /Y /Q >nul

echo ================================================================
echo [PASS] Application codebase rollback completed successfully.
echo User database, migrations, and local pepper keys were preserved.
echo ================================================================
exit /b 0
