#!/bin/bash
# Scheduled Daily Audit for DevBase
# Runs consistency checks and auto-fixes documentation debt.

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.." || exit 1

echo "Running Daily Consistency Audit..."
uv run python src/devbase/main.py --root . audit run --fix --days 1
