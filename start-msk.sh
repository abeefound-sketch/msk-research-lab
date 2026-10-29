#!/usr/bin/env bash
# MSK Therapy Personal Workstation Launcher (WSL / Linux)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "       MSK THERAPY PERSONAL WORKSTATION (TASK 05P)              "
echo "       Constraint-First * Local-First * Evidence-First          "
echo "================================================================"

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON_BIN="$VIRTUAL_ENV/bin/python"
    elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
    elif command -v python3 &>/dev/null; then
        PYTHON_BIN="python3"
    elif command -v python &>/dev/null; then
        PYTHON_BIN="python"
    else
        echo "ERROR: Python 3 executable not found in .venv or PATH."
        echo "Please install Python 3.10+ and run: python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
        exit 1
    fi
fi

echo "[1/3] Python Runtime: $PYTHON_BIN ($($PYTHON_BIN --version))"
export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"

echo "[2/3] Verified PYTHONPATH: $PYTHONPATH"
echo "[3/3] Launching Workstation on http://127.0.0.1:8000 ..."
echo ""

exec "$PYTHON_BIN" -m msk_research_lab workstation --port 8000 "$@"
