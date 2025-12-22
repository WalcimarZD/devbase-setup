#!/usr/bin/env python3
"""
DEPRECATED: Legacy DevBase CLI
================================
This file is deprecated. The project has migrated to a modern src-layout structure.

Please use one of the following instead:
  - Installed command: `devbase` (after uv tool install or pipx install)
  - Development mode: `uv run devbase` or `python -m devbase`
  - Direct execution: `python src/devbase/main.py`

For migration details, see: MIGRATION.md
"""
import sys

print("⚠️  WARNING: This is the LEGACY CLI (deprecated)")
print("")
print("The DevBase project has been modernized with:")
print("  • Modern packaging (PEP 621 + uv)")
print("  • Typer-based CLI framework")
print("  • Rich terminal UI")
print("")
print("Please use instead:")
print("  devbase          # If installed via 'uv tool install' or 'pipx install'")
print("  uv run devbase   # For development")
print("")
print("For details, see: README.md or MIGRATION.md")
print("")
sys.exit(1)
