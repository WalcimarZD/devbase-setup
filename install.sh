#!/bin/bash
# DevBase Universal Installer
# Wrapper script to bootstrap the environment on Linux/macOS

set -e

echo "=== DevBase Installer v3.1 ==="

# 1. Check for PowerShell (Preferred for v3 full feature set)
if command -v pwsh &> /dev/null; then
    echo " [✓] PowerShell Core (pwsh) detected."
    echo "     Running full bootstrap..."
    pwsh -NoProfile -ExecutionPolicy Bypass -File ./bootstrap.ps1 "$@"
    exit 0
fi

# 2. Fallback to Python (v4 Preview / Core Features)
if command -v python3 &> /dev/null; then
    echo " [!] PowerShell not found."
    echo " [✓] Python 3 detected."
    echo "     Running Python bootstrap (Core features only)..."
    python3 ./devbase.py "$@"
    exit 0
fi

# 3. Failure
echo " [X] Error: Neither 'pwsh' nor 'python3' found."
echo "     Please install PowerShell Core or Python 3 to continue."
exit 1