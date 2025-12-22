# DevBase Architecture

## Overview

DevBase is a **Personal Engineering Operating System** built on Python with a modular architecture.

```
┌─────────────────────────────────────────────────────────────┐
│                      devbase cli (Typer)                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │   core    │ │    dev    │ │    ops    │ │    nav    │    │
│  │ (setup+)  │ │ (new+)    │ │ (track+)  │ │ (goto)    │    │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘    │
└────────┼─────────────┼─────────────┼─────────────┼──────────┘
         │             │             │             │
┌────────▼─────────────▼─────────────▼─────────────▼──────────┐
│                    src/devbase/                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │   commands/  │ │   legacy/    │ │  templates/  │         │
│  │ (core, dev+) │ │ (fs, state)  │ │ (jinja2)     │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
└─────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│  Dev_Workspace/   │         │   .telemetry/     │
│  (Johnny.Decimal) │         │   events.jsonl    │
└───────────────────┘         └───────────────────┘
```

## Components

### CLI Layer (Typer)

Managed via `src/devbase/main.py` and modular command groups in `src/devbase/commands/`:

| Group | Function | Description |
|-------|----------|-------------|
| `core` | `commands/core.py` | Setup, Doctor, Hydrate |
| `dev` | `commands/dev.py` | New, Audit, Templates |
| `ops` | `commands/ops.py` | Track, Stats, Weekly, Backup, Clean |
| `nav` | `commands/nav.py` | Semantic navigation (goto) |
| `quick` | `commands/quick.py` | Macro commands (sync, quickstart) |
| `pkm` | `commands/pkm.py` | PKM analysis (graph, links, index) |

### Core Logic (Legacy & Modern)

| Module | Purpose |
|--------|---------|
| `legacy/filesystem.py` | Atomic file operations with dry-run support |
| `legacy/ui.py` | Colorized console output helpers |
| `legacy/state.py` | State management (`.devbase_state.json`) |
| `utils/wizard.py` | Interactive setup wizard |
| `utils/icons.py` | Johnny.Decimal folder icon management |
| `templates/` | Jinja2 templates for projects and knowledge |

### Data Layer

| File/Folder | Purpose |
|-------------|---------|
| `.devbase_state.json` | Installation state and version |
| `.telemetry/events.jsonl` | Activity tracking (JSON Lines) |
| `30-39_OPERATIONS/31_backups/` | Backup storage |

## Key Patterns

### 1. Atomic File Operations

```python
# filesystem.py uses write-replace pattern
with open(tmp_path, 'w') as f:
    f.write(content)
    f.flush()
    os.fsync(f.fileno())
tmp_path.replace(target)  # Atomic on POSIX/Windows
```

### 2. Dry-Run Mode

```python
class FileSystem:
    def __init__(self, root, dry_run=False):
        self.dry_run = dry_run
    
    def ensure_dir(self, path):
        if self.dry_run:
            print(f" [DRY-RUN] Would create: {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
```

### 3. Johnny.Decimal Structure

```
XX-YY_AREA/
  XX_category/
    item/
```

Areas: 00-09, 10-19, 20-29, 30-39, 40-49, 90-99

### 4. Telemetry (JSON Lines)

```json
{"timestamp": "2025-12-11T10:00:00", "type": "work", "message": "Feature X"}
{"timestamp": "2025-12-11T11:00:00", "type": "meeting", "message": "Standup"}
```

## Dashboard Architecture

```
dashboard/
├── server.py          # Flask routes (/api/stats, /api/activity)
├── templates/
│   └── index.html     # Main dashboard page
└── static/
    ├── style.css      # Dark theme styling
    └── charts.js      # Chart.js integration
```

## VS Code Extension

```
vscode-devbase/
├── src/
│   ├── extension.ts           # Entry point
│   ├── commands/index.ts      # Command implementations
│   └── providers/
│       ├── structureProvider.ts    # Johnny.Decimal tree
│       └── recentActivityProvider.ts
├── snippets/
│   └── devbase.code-snippets  # ADR, TIL, Journal
└── package.json               # Extension manifest
```
