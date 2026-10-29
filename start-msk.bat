@echo off
TITLE MSK Therapy Personal Workstation Launcher
COLOR 0B
echo ================================================================
echo        MSK THERAPY PERSONAL WORKSTATION (TASK 05P)
echo        Constraint-First * Local-First * Evidence-First
echo ================================================================
echo.

set WORKDIR=%~dp0
cd /d "%WORKDIR%"

:: Locate Python Runtime (prefer Windows native venv with OpenCV/MediaPipe/Camera access)
set PYTHON_EXE=
if exist "C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=C:\Users\tuanh\MSK-Pose-Vision-Bridge\.venv\Scripts\python.exe"
) else if exist "%WORKDIR%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%WORKDIR%\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1/3] Python Runtime: %PYTHON_EXE%
"%PYTHON_EXE%" --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python runtime not found at %PYTHON_EXE%
    echo Please ensure Python 3.10+ is installed and accessible.
    pause
    exit /b 1
)

echo [2/3] Setting PYTHONPATH to %WORKDIR%src
set "PYTHONPATH=%WORKDIR%src;%PYTHONPATH%"

echo [3/3] Launching MSK Therapy Personal Workstation on http://127.0.0.1:8000 ...
echo.
"%PYTHON_EXE%" -m msk_research_lab workstation --port 8000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application stopped with exit code %ERRORLEVEL%.
    pause
)
