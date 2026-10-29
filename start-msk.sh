#!/usr/bin/env bash
# MSK Therapy Personal Workstation Launcher (WSL / Linux)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "       MSK THERAPY PERSONAL WORKSTATION (TASK 05P)              "
echo "       Constraint-First * Local-First * Evidence-First          "
echo "================================================================"

PYTHON_BIN=""
if [ -f "/home/tuan/.venvs/msk-lab/bin/python" ]; then
    PYTHON_BIN="/home/tuan/.venvs/msk-lab/bin/python"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    echo "ERROR: Python 3 executable not found."
    exit 1
fi

echo "[1/3] Python Runtime: $PYTHON_BIN ($($PYTHON_BIN --version))"
export PYTHONPATH="$SCRIPT_DIR/src:${PYTHONPATH:-}"

echo "[2/3] Verified PYTHONPATH: $PYTHONPATH"
echo "[3/3] Launching Workstation on http://127.0.0.1:8000 ..."
echo ""

exec "$PYTHON_BIN" -m msk_research_lab workstation --port 8000 "$@"
