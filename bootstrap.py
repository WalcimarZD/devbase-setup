#!/usr/bin/env python3
"""
DevBase CLI Shim
================
This script ensures the CLI can be run directly from the root directory
without installation, mirroring the behavior of the installed `devbase` command.
"""
import sys
from pathlib import Path

# Add src to python path to allow direct import
PROCESS_ROOT = Path(__file__).parent.resolve()
SRC_PATH = PROCESS_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

try:
    from devbase.main import cli_main
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import DevBase CLI: {e}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

if __name__ == "__main__":
    cli_main()
