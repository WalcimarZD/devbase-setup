#!/bin/bash
# Daily Consistency Audit
# Runs devbase consistency audit and fixes minor issues

set -e

echo "Starting Daily Audit..."

# Navigate to repo root (assuming script is in scripts/)
cd "$(dirname "$0")/.."

# Run audit with --fix enabled
# Using uv run to ensure environment consistency
# Note: --root must be passed before the subcommand 'audit'
uv run devbase --root . audit run --fix --days 1

echo "Audit Complete."
