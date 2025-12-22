# DevBase v4.0 - Migration Guide

## Overview

DevBase v4.0 is a **complete rewrite** using modern Python tooling for significantly improved developer experience.

## Key Changes

### 1. Installation Method

**v3.x:**
```bash
git clone https://github.com/walcimarzd/devbase-setup
python devbase.py --help
```

**v4.0:**
```bash
uv tool install devbase
devbase --help
```

### 2. Command Structure

Commands are now organized into **groups** for better discoverability:

**v3.x:**
```bash
python devbase.py doctor
python devbase.py new my-app
python devbase.py track "message"
```

**v4.0:**
```bash
devbase core doctor
devbase dev new my-app
devbase ops track "message"
```

### 3. Workspace Detection

**v3.x:** Required `--root` flag on every command
```bash
cd ~/somewhere
python devbase.py doctor --root ~/Dev_Workspace
```

**v4.0:** Auto-detects workspace
```bash
cd ~/Dev_Workspace/20-29_CODE/my-project
devbase core doctor  # Works from any subdirectory!
```

### 4. Global Availability

**v3.x:** Must run from repository directory
```bash
cd ~/devbase-setup
python devbase.py new my-app
```

**v4.0:** Works from anywhere
```bash
cd ~
devbase dev new my-app  # Just works ✨
```

## Complete Command Mapping

| v3.x | v4.0 | Notes |
|------|------|-------|
| `setup` | `core setup` | Now has interactive wizard |
| `doctor` | `core doctor` | Displays Rich tables |
| `hydrate` | `core hydrate` | Unchanged |
| `new -Name <name>` | `dev new <name>` | Positional argument |
| `audit` | `dev audit` | Same |
| `audit -Fix` | `dev audit --fix` | Flag renamed |
| `track -Message "x"` | `ops track "x"` | Positional message |
| `stats` | `ops stats` | Now uses Rich tables |
| `weekly` | `ops weekly` | Same |
| `weekly -Output file` | `ops weekly --output file` | Flag renamed |
| `backup` | `ops backup` | Same |
| `clean` | `ops clean` | Same |

## Migration Steps

### Step 1: Install v4.0

```bash
# Uninstall old scripts (if applicable)
# No action needed if you were running from source

# Install v4.0 globally
uv tool install devbase

# Verify
devbase --help
```

### Step 2: Update Scripts/Aliases

If you have shell scripts or aliases referencing DevBase:

**Before:**
```bash
alias db-doctor="cd ~/devbase-setup && python devbase.py doctor --root ~/Dev_Workspace"
```

**After:**
```bash
alias db-doctor="devbase core doctor"
```

### Step 3: Update CI/CD Pipelines

**GitHub Actions Example:**

**v3.x:**
```yaml
- name: Setup DevBase
  run: |
    git clone https://github.com/walcimarzd/devbase-setup
    python devbase-setup/devbase.py setup --root ./workspace
```

**v4.0:**
```yaml
- name: Setup DevBase
  run: |
    uv tool install devbase
    devbase core setup  # Auto-creates at ~/Dev_Workspace
```

## Breaking Changes

### Python Module Imports

**v3.x:**
```python
# Direct imports from modules/python/
from filesystem import FileSystem
from state import StateManager
```

**v4.0:**
```python
# Proper package imports
from devbase.utils.filesystem import FileSystem
from devbase.utils.state import StateManager
```

### Configuration

- `.devbase_state.json` format unchanged
- `pyproject.toml` replaces `requirements.txt`
- Ruff replaces flake8/black/isort

## Compatibility

### What Still Works

✅ Existing workspaces (no migration needed)
✅ `.devbase_state.json` format
✅ Johnny.Decimal structure
✅ Templates
✅ Telemetry data (`.telemetry/events.jsonl`)

### What's Removed

❌ PowerShell fallback (`devbase.ps1`)
❌ `argparse`-based CLI
❌ `requirements.txt`

## Rollback Plan

If you need to revert to v3.x:

```bash
# Uninstall v4.0
uv tool uninstall devbase

# Use v3.x from source
git clone https://github.com/walcimarzd/devbase-setup --branch v3.2
cd devbase-setup
python devbase.py --help
```

## Support

- Report issues: https://github.com/walcimarzd/devbase-setup/issues
- Tag with `migration` label
