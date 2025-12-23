#!/bin/bash
# DevBase Universal Installer
# Wrapper script to bootstrap the environment on Linux/macOS

set -e

echo "=== DevBase Installer v3.1 ==="

# 1. Check for 'uv' (Recommended)
if command -v uv &> /dev/null; then
    echo " [✓] 'uv' detected. Bootstrapping with high-speed installer..."
    uv run python bootstrap.py "$@"
    exit 0
fi

# 2. Fallback to standard Python
if command -v python3 &> /dev/null; then
    echo " [✓] Python 3 detected."
    echo "     Installing dependencies and running setup..."
    python3 -m pip install --user uv &> /dev/null || true
    python3 ./bootstrap.py "$@"
    exit 0
fi

# 3. Failure
echo " [X] Error: Python 3.10+ required but not found."
echo "     Please install Python from https://python.org"
exit 1
