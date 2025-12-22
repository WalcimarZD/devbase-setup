# DevBase v4.0 - Modern Python CLI 🚀

**Personal Engineering Operating System** built with Typer, Rich, and uv.

> [!IMPORTANT]
> This is **v4.0** - a complete rewrite using modern Python tooling.
> Migrating from v3.x? See [MIGRATION.md](MIGRATION.md)

## Quick Start

### Installation (Global CLI)

```bash
# Install with uv (recommended)
uv tool install devbase

# Install with pipx
pipx install devbase

# Verify installation
devbase --help
```

### 5-Second Setup

```bash
devbase core setup
# Follow interactive prompts
```

That's it! You now have a complete Johnny.Decimal workspace at `~/Dev_Workspace`.

## What's New in v4.0?

✨ **Modern Stack**:
- 🔷 **Typer** - Type-safe CLI (replaces argparse)
- 🎨 **Rich** - Beautiful terminal output
- ⚡ **uv** - 100x faster Python package management
- 🔧 **Ruff** - Instant linting & formatting

✨ **Usability Improvements**:
- 🔍 **Auto-detection** of workspace (no more `--root` flag)
- 🧙 **Interactive wizard** for first-time setup
- 🎯 **Context-aware** commands
- 📦 **Global installation** (`devbase` works from anywhere)

✨ **Better DevX**:
- 📖 Auto-generated help with examples
- 🎭 Rich status indicators & progress bars
- 🔒 Strong type safety
- ⚡ 10x faster operations

## Command Groups

### Core Workspace Management

```bash
devbase core setup      # Initialize workspace with interactive wizard 🧙
devbase core doctor     # Health check with rich diagnostics
devbase core hydrate    # Update templates from source
```

### Development & Templates

```bash
# Interactive project creation (recommended)
devbase dev new my-app

# Specific template queries
devbase dev new my-api --template api
devbase dev new my-lib --no-interactive

# Code quality
devbase dev audit       # Check naming conventions
devbase dev audit --fix # Auto-fix violations
```

### Operations & Context-Awareness

```bash
# Context-aware tracking (auto-detects project & type)
cd my-project
devbase ops track "Implemented feature X"  # tag: [coding:my-project]

# Manual tracking
devbase ops track "Meeting notes" --type meeting

# Analytics & Maintenance
devbase ops stats                      # View activity stats
devbase ops weekly --output report.md  # Generate weekly report
devbase ops backup                     # Create incremental backup
devbase ops clean                      # Remove temp files
```

### Semantic Navigation

```bash
devbase nav goto code      # → 20-29_CODE/21_monorepo_apps
devbase nav goto vault     # → 10-19_KNOWLEDGE/12_private_vault
devbase nav goto ai        # → 30-39_OPERATIONS/30_ai

# Shell integration (add to RC file):
goto code                  # Jump directly!
```

### Quick Actions

```bash
devbase quick quickstart my-app  # Create + Git Init + VS Code 🚀
devbase quick sync               # Doctor + Hydrate + Backup 🔄
```

## Example Workflow

```bash
# Day 1: Setup
devbase core setup
# ... follow interactive prompts ...

# Day 2: Create project
devbase dev new my-api
cd 20-29_CODE/21_monorepo_apps/my-api

# Day 3: Track work
devbase ops track "Implemented OAuth2 authentication"

# Friday: Generate report
devbase ops weekly --output ~/weeknotes.md
```

## Architecture

```
~/Dev_Workspace/
├── 00-09_SYSTEM/       # Configuration & dotfiles
├── 10-19_KNOWLEDGE/    # PKM, notes, decisions
├── 20-29_CODE/         # Source code projects
├── 30-39_OPERATIONS/   # Automation, backups, AI
├── 40-49_MEDIA_ASSETS/ # Media files
└── 90-99_ARCHIVE_COLD/ # Archived projects
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the Johnny.Decimal methodology.

## Configuration

DevBase v4.0 supports user configuration via `~/.devbase/config.toml`:

```toml
[workspace]
auto_detect = true

[behavior]
expert_mode = false
color_output = true

[telemetry]
enabled = true
```

## Development

### Setup Dev Environment

```bash
# Clone repository
git clone https://github.com/walcimarzd/devbase-setup
cd devbase-setup

# Install with uv (creates .venv automatically)
uv sync

# Install in editable mode
uv pip install -e .

# Run from source
uv run devbase --help
```

### Running Tests

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=devbase

# Run specific test
uv run pytest tests/test_workspace.py -v
```

### Code Quality

```bash
# Lint & format with Ruff
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy src/
```

## Migration from v3.x

v4.0 introduces breaking changes:

| v3.x | v4.0 |
|------|------|
| `python devbase.py doctor` | `devbase core doctor` |
| `devbase new my-app` | `devbase dev new my-app` |
| `devbase track "msg"` | `devbase ops track "msg"` |
| Must specify `--root` | Auto-detected ✨ |
| `argparse` CLI | Typer CLI ✨ |

See [MIGRATION.md](MIGRATION.md) for full details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT © DevBase Team

---

**Questions?** Open an [issue](https://github.com/walcimarzd/devbase-setup/issues).
**Documentation:** [https://walcimarzd.github.io/devbase-setup/](https://walcimarzd.github.io/devbase-setup/)
