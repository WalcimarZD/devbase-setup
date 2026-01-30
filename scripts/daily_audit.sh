#!/bin/bash
set -e

# Run consistency audit
# --root . is essential to run in repo context
# --fix enables auto-fixing (appending to docs)
# --days 1 checks last 24h
echo "Running Daily Consistency Audit..."
uv run devbase --root . audit run --fix --days 1
