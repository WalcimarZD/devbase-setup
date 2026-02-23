# DevBase v5.1.0-alpha.1 🚀

**The Personal Engineering Operating System**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://python.org)
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
- **Documentation Engine**: Standardized ADRs, Guides, and Specs via `devbase docs`.
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
| *(New in v5)* | `devbase docs new` | **Standardized documentation generator** |

> **Upgrading?** See [MIGRATION.md](MIGRATION.md) for a complete guide on moving from v4.

---

## 🛠️ Troubleshooting

- **Python SyntaxError on startup**: DevBase v5 requires **Python 3.13+**. Ensure your `uv` environment or global python is updated.
- **`uv` Cache Errors**: If you encounter dependency resolution issues, step back and run `uv cache clean`, then retry the installation.
- **Database Lock**: If the CLI hangs unexpectedly, ensure no other DevBase instance is actively writing to the local DuckDB telemetry database.

---

## 📚 Documentation

Our documentation is structured according to the [Diataxis Framework](https://diataxis.fr/) to reduce cognitive load and provide a zero-friction developer experience.

- 🎓 **[Tutorials](docs/tutorials/)**: Learning-oriented guides for entering the DevBase ecosystem.
- 🎯 **[How-To Guides](docs/how-to/)**: Goal-oriented recipes for common tasks (e.g., adding new project templates).
- 📖 **[Reference](docs/)**: Information-oriented technical specifications, including the [USAGE-GUIDE](USAGE-GUIDE.md) and [ARCHITECTURE](ARCHITECTURE.md).
- 💡 **[Explanation](docs/explanation/)**: Understanding-oriented background knowledge discussing design choices and system methodology.

> For contributing, see [CONTRIBUTING.md](CONTRIBUTING.md).
