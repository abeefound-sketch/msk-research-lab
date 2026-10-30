@echo off
setlocal enabledelayedexpansion
TITLE MSK Therapy Personal Workstation Launcher
COLOR 0B
echo ================================================================
echo        MSK THERAPY PERSONAL WORKSTATION (TASK 05P)
echo        Constraint-First * Local-First * Evidence-First
echo ================================================================
echo.

set "WORKDIR=%~dp0"
cd /d "%WORKDIR%"

:: 1. Check explicit environment override
if defined PYTHON_EXE if exist "%PYTHON_EXE%" goto :found_python

:: 2. Check active virtual environment
if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
    set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
    goto :found_python
)

:: 3. Check workspace .venv (native Windows)
if exist "%WORKDIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%WORKDIR%.venv\Scripts\python.exe"
    goto :found_python
)

:: 4. Check user MSK-Pose-Vision-Bridge virtualenv
if exist "%USERPROFILE%\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe"
    goto :found_python
)

:: 5. Check system Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=python"
    goto :found_python
)

goto :try_wsl

:found_python
echo [1/3] Python Runtime: %PYTHON_EXE%
"%PYTHON_EXE%" -c "import fastapi, uvicorn" >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :launch_native

echo [WARN] %PYTHON_EXE% is missing required dependencies (fastapi/uvicorn).

:try_wsl
where wsl >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :no_runtime

echo [INFO] Launching via WSL2 environment where dependencies are installed...
wsl -e bash -c "cd \"$(wslpath '%WORKDIR%')\" && bash start-msk.sh %*"
exit /b %ERRORLEVEL%

:no_runtime
echo ERROR: Python 3 runtime not found or lacks required dependencies.
echo Please ensure Python 3.10+ is installed and accessible.
pause
exit /b 1

:launch_native
echo [2/3] Setting PYTHONPATH to %WORKDIR%src
set "PYTHONPATH=%WORKDIR%src;%PYTHONPATH%"

echo [3/3] Launching MSK Therapy Personal Workstation on http://127.0.0.1:8000 ...
echo.
"%PYTHON_EXE%" -m msk_research_lab workstation --port 8000 %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application stopped with exit code %ERRORLEVEL%.
    pause
)
