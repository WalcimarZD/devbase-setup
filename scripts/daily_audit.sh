#!/bin/bash
# Daily Audit Script for DevBase
# Runs consistency checks and auto-fixes documentation

echo "Starting Daily Audit..."

# Navigate to repo root if needed, or assume running from root
# Detect if uv is available
if command -v uv >/dev/null 2>&1; then
    uv run python src/devbase/main.py --root . audit run --fix --days 1
else
    echo "Error: uv not found. Please install uv or run in a devbase environment."
    exit 1
fi
