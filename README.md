# DevBase v5.1.0-alpha.1 🚀

**The Personal Engineering Operating System**

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Typer](https://img.shields.io/badge/CLI-Typer-white.svg)](https://typer.tiangolo.com)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**DevBase** is a modular CLI that transforms your chaos into a structured, high-performance engineering workspace. Built on the [Johnny.Decimal](https://johnnydecimal.com) methodology, it organizes your code, knowledge, and operations into a standard, navigable directory tree.

> [!NOTE]
> **v5.1.0 (The "Intelligence" Release)**: This version introduces the AI module, empowering your workspace with LLM-driven organization and insights, while maintaining the high-speed Python core.

---

## ⚡ Productivity First

- **Zero-Config Workspace**: Auto-detects your `Dev_Workspace` root from anywhere.
- **AI-Powered Organization**: Let `devbase ai` handle your file sorting and structure optimization.
- **Instant Project Scaffolding**: Generate production-ready Clean Architecture boilerplate in seconds.
- **Knowledge Graph**: Integrated Personal Knowledge Management (PKM) with backlinking.
- **Context-Aware Analytics**: Track your "Flow State" and generate weekly summaries automatically.

## 🚀 Installation

### Option A: The One-Liner (Recommended)
Installs `uv`, Python 3.13, and DevBase in an isolated environment.

```bash
curl -Ls https://raw.githubusercontent.com/walcimarzd/devbase-setup/main/install.sh | bash
```

### Option B: Power Users (`uv`)
If you already have `uv` installed:

```bash
uv tool install devbase
```

*Verify installation:*
```bash
devbase --version
# Output: devbase 5.1.0-alpha.1
```

---

## ⏱️ Quick Start: 30 Seconds to Flow

1. **Initialize Workspace**
   Creates the Johnny.Decimal structure (Code, Knowledge, Operations) and installs governance files.
   ```bash
   devbase core setup
   ```

2. **Create New Project**
   Scaffolds a new API with Git, pre-commit hooks, and VS Code settings.
   ```bash
   devbase dev new my-awesome-api
   ```

3. **Track Your Work**
   Log your progress directly to the local telemetry database.
   ```bash
   devbase ops track "Initial commit for my-awesome-api"
   ```

---

## 🔄 Migration Parity (v4 vs v5)

DevBase v5.0.0 replaces all legacy PowerShell scripts with standard CLI subcommands.

| Legacy (v4 PowerShell) | Modern (v5 Python) | Benefit |
| :--- | :--- | :--- |
| `./bootstrap.ps1` | `devbase core setup` | Interactive wizard, better error handling |
| `devbase.py doctor` | `devbase core doctor` | Rich visuals, auto-fix capabilities |
| `devbase.py new ...` | `devbase dev new ...` | Faster templating, `copier` integration |
| `devbase.py track` | `devbase ops track` | Context-aware, lower latency |
| `devbase.py stats` | `devbase ops stats` | DuckDB-powered analytics |

> **Upgrading?** See [MIGRATION.md](MIGRATION.md) for a complete guide on moving from v4.

---

## 📚 Documentation

- [**USAGE-GUIDE.md**](USAGE-GUIDE.md): The complete field manual for all commands.
- [**ARCHITECTURE.md**](ARCHITECTURE.md): Deep dive into the Command-Service-Adapter pattern.
- [**CONTRIBUTING.md**](CONTRIBUTING.md): How to build your own plugins and templates.
