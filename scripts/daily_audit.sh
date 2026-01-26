#!/bin/bash
# scripts/daily_audit.sh
# Runs the daily consistency audit

# Ensure we are in the repo root
cd "$(dirname "$0")/.."

# Run the audit
echo "Running DevBase Consistency Audit..."
uv run python src/devbase/main.py --root . audit run --fix --days 1
