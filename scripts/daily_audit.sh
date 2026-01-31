#!/bin/bash
set -e

# Run the consistency audit
echo "Starting Daily Consistency Audit..."
uv run devbase --root . audit run --fix --days 1
echo "Audit complete."
