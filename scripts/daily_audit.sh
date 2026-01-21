#!/bin/bash
# ==============================================================================
# Daily Consistency Audit for DevBase
# ==============================================================================
# This script is designed to be run as a daily cron job.
# It runs the `devbase audit run` command with auto-fix enabled to ensure
# consistency between code and documentation.
#
# Usage (Crontab):
# 0 9 * * * /path/to/repo/scripts/daily_audit.sh >> /path/to/logs/audit.log 2>&1
# ==============================================================================

# Ensure we are in the project root if the script is run from elsewhere
# Resolves the directory where the script is located, then goes up one level
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || { echo "Failed to cd to $PROJECT_ROOT"; exit 1; }

# Timestamp for log
echo "------------------------------------------------------------------------"
echo "Running Daily Audit: $(date)"
echo "------------------------------------------------------------------------"

# Detect execution method (uv or python direct)
if command -v uv &> /dev/null; then
    # Use uv if available (preferred for this project)
    # We pass --root . to ensure it runs in the current repo context even if no workspace is active
    uv run python src/devbase/main.py --root . audit run --fix
else
    # Fallback to python if PYTHONPATH is set or we are in a simple env
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    python3 src/devbase/main.py --root . audit run --fix
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Audit completed successfully."
else
    echo "Audit finished with warnings or errors (Exit Code: $EXIT_CODE)."
fi

echo "------------------------------------------------------------------------"
