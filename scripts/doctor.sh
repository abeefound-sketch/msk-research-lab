#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo " MSK Research Lab OS: Environment Doctor "
echo "========================================="

echo "[1/4] Checking OS and Kernel..."
uname -a

echo "[2/4] Checking Python version..."
python3 --version

echo "[3/4] Checking memory (Target: >=8GB RAM)..."
free -h

echo "[4/4] Checking disk space..."
df -h .

echo "Doctor check complete."
