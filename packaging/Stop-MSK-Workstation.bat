@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo MSK Research Lab OS — Workstation Shutdown Utility
echo ================================================================

set TARGET_PORT=8091
set FOUND_PID=

for /f "tokens=5" %%a in ('netstat -ano -p tcp ^| findstr ":%TARGET_PORT% "') do (
    set FOUND_PID=%%a
)

if "%FOUND_PID%"=="" (
    echo [INFO] No active MSK Research Lab Workstation process found listening on port %TARGET_PORT%.
    exit /b 0
)

echo [INFO] Terminating MSK Research Lab process (PID: %FOUND_PID%) on port %TARGET_PORT%...
taskkill /F /PID %FOUND_PID% >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [PASS] MSK Research Lab Workstation stopped successfully.
) else (
    echo [WARN] Unable to terminate PID %FOUND_PID%. It may have already exited.
)

exit /b 0
