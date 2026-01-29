#!/bin/bash
set -e

# Ensure we are in the repo root
cd "$(dirname "$0")/.."

# Ensure .devbase_state.json exists for devbase command to work
if [ ! -f ".devbase_state.json" ]; then
  echo "Creating temporary .devbase_state.json for audit..."
  echo '{"version": "5.1.0", "created_at": "2024-01-01T00:00:00"}' > .devbase_state.json
fi

# Run the audit command
# We use 'uv run' to ensure dependencies are installed and used
echo "Running daily audit..."
uv run devbase audit run --fix --days 1
