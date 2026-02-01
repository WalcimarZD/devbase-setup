#!/bin/bash
set -e

# Daily Consistency Audit Script
# ==============================
# Runs the DevBase consistency audit to ensure code and docs are aligned.
# Designed to be run by GitHub Actions or local cron.

echo "Running DevBase Consistency Audit..."

# Ensure we are at the repo root
cd "$(dirname "$0")/.."

# Install/Sync dependencies just in case
if command -v uv >/dev/null 2>&1; then
    uv sync --quiet
else
    echo "Error: uv is not installed."
    exit 1
fi

# Run the audit command
# --root . : Forces the current directory as workspace root (bypassing user workspace)
# --fix    : Automatically fixes USAGE-GUIDE.md and CHANGELOG.md
# --days 1 : Checks changes in the last 24 hours
uv run devbase --root . audit run --fix --days 1

echo "Audit complete."
