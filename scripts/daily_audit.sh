#!/bin/bash
set -e

# Daily Audit Script
# Runs the DevBase consistency audit to ensure code and docs are aligned.

echo "🔍 Starting Daily Consistency Audit..."

# Ensure we are in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the project root."
    exit 1
fi

# Run the audit command
# Using uv run to use the project's virtual environment
uv run python src/devbase/main.py --root . audit run --fix --days 1

echo "✅ Audit complete."
