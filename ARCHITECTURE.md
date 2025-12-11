# DevBase Architecture

## Overview

DevBase is a **Personal Engineering Operating System** built on Python with a modular architecture.

```
┌─────────────────────────────────────────────────────────────┐
│                      devbase.py (CLI)                       │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │
│  │  setup  │ doctor  │  audit  │  track  │dashboard│       │
│  └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘       │
└───────┼─────────┼─────────┼─────────┼─────────┼─────────────┘
        │         │         │         │         │
┌───────▼─────────▼─────────▼─────────▼─────────▼─────────────┐
│                    modules/python/                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │filesystem│ │    ui    │ │   state  │ │   dashboard  │   │
│  │  .py     │ │   .py    │ │   .py    │ │   /server.py │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │setup_core│ │setup_pkm │ │setup_code│  ...more modules   │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
        │                               │
        ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│  Dev_Workspace/   │         │   .telemetry/     │
│  (Johnny.Decimal) │         │   events.jsonl    │
└───────────────────┘         └───────────────────┘
```

## Components

### CLI Layer (`devbase.py`)

The main entry point using `argparse` with subcommands:

| Command | Function | Description |
|---------|----------|-------------|
| `setup` | `cmd_setup()` | Initialize workspace |
| `doctor` | `cmd_doctor()` | Health check |
| `audit` | `cmd_audit()` | Naming convention check |
| `new` | `cmd_new()` | Create project from template |
| `hydrate` | `cmd_hydrate()` | Sync templates |
| `backup` | `cmd_backup()` | 3-2-1 backup |
| `clean` | `cmd_clean()` | Remove temp files |
| `track` | `cmd_track()` | Log activity |
| `stats` | `cmd_stats()` | Show statistics |
| `weekly` | `cmd_weekly()` | Weekly report |
| `dashboard` | `cmd_dashboard()` | Web dashboard |

### Modules Layer (`modules/python/`)

| Module | Purpose |
|--------|---------|
| `filesystem.py` | Atomic file operations with dry-run support |
| `ui.py` | Console output formatting |
| `state.py` | State management (`.devbase_state.json`) |
| `setup_*.py` | Individual setup modules |
| `dashboard/` | Flask web dashboard |

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
