#!/bin/bash
# Daily Consistency Audit for DevBase
# ===================================
# Scans code/docs consistency and auto-fixes where possible.
#
# Setup (Cron):
# 0 18 * * * /path/to/devbase/scripts/daily_audit.sh >> /path/to/devbase/audit.log 2>&1

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo "---------------------------------------------------"
echo "Starting Audit: $(date)"
echo "---------------------------------------------------"

# Check if uv is installed (preferred runner)
if command -v uv &> /dev/null; then
    echo "Using uv run..."
    uv run devbase --root . audit run --fix --days 1
elif command -v devbase &> /dev/null; then
    echo "Using installed devbase..."
    devbase --root . audit run --fix --days 1
else
    echo "Using python source..."
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    python3 src/devbase/main.py --root . audit run --fix --days 1
fi

echo "---------------------------------------------------"
echo "Audit Complete: $(date)"
echo "---------------------------------------------------"
