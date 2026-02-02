#!/bin/bash
set -e

# Run consistency audit
# Fixes issues automatically where possible
# Checks changes in last 24 hours (default days=1)
uv run devbase --root . audit run --fix --days 1
