#!/bin/bash
# Daily Consistency Audit
# Runs the devbase audit command to ensure code and docs are in sync.

# Ensure we are at the project root
cd "$(dirname "$0")/.."

echo "Running Daily Consistency Audit..."
uv run devbase --root . audit run --fix --days 1
