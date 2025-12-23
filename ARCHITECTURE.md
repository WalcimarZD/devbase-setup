# Architecture Guide: DevBase v5.0.0

This document explains the internal design of DevBase, intended for contributors and maintainers.

## 🏗️ High-Level Design

DevBase v5.0.0 follows a strict **Command-Service-Adapter** pattern to ensure testability, separation of concerns, and modularity.

```mermaid
graph TD
    CLI[CLI Layer (Typer)] -->|Context| Service[Service Layer]
    Service -->|DTO| Adapter[Adapter Layer]
    Adapter -->|IO| FS[Filesystem / OS]
    Adapter -->|SQL| DB[DuckDB / SQLite]
```

### 1. CLI Layer (`src/devbase/commands`)
- **Technology**: `typer` + `rich`
- **Role**: Entry point. Handles argument parsing, validation, and UI output.
- **Rules**:
    - NO business logic.
    - MUST catch exceptions and print friendly errors.
    - MUST use `rich` for all output.

### 2. Service Layer (`src/devbase/services`)
- **Technology**: Pure Python
- **Role**: Orchestrates business logic.
- **Rules**:
    - Platform-agnostic.
    - Does NOT print to console (returns data/objects).
    - Can be imported by other services.

### 3. Adapter Layer (`src/devbase/utils` & `src/devbase/adapters`)
- **Technology**: `pathlib`, `json`, `duckdb`
- **Role**: Interfaces with the outside world.
- **Rules**:
    - Handles low-level I/O.
    - Implements "Dry Run" logic.
    - Manages state persistence (`.devbase_state.json`).

---

## 🛠️ Technology Stack

| Component | Library | Reason |
| :--- | :--- | :--- |
| **CLI Framework** | `typer` | Modern, type-safe, practically zero boilerplate. |
| **Terminal UI** | `rich` | Beautiful output, tables, and progress bars are essential for DX. |
| **Packaging** | `uv` | Orders of magnitude faster than Pip/Poetry. Simplifies venv management. |
| **Analytics** | `duckdb` | Embedded OLAP database for fast querying of telemetry logs. |
| **Templating** | `jinja2` | Industry standard, flexible, sandboxed. |

---

## 📂 Project Structure

```text
src/devbase/
├── main.py              # Application Entry Point
├── commands/            # CLI Groups
│   ├── core.py          # Setup, Doctor
│   ├── dev.py           # Project Management
│   ├── ops.py           # Operations & Telemetry
│   └── pkm.py           # Knowledge Graph
├── services/            # Business Logic
│   └── project_setup.py # Project scaffolding service
├── utils/               # Shared Utilities
│   ├── filesystem.py    # Atomic file operations
│   ├── wizard.py        # Interactive prompts
│   └── telemetry.py     # Event logging
└── templates/           # Jinja2 Templates
```

---

## 🔄 Data Flow: "Creating a Project"

When a user runs `devbase dev new my-api`:

1.  **CLI (`commands/dev.py`)**:
    - Parses `my-api`.
    - Detects `--interactive` flag.
    - Instantiates `Console` and `Context`.

2.  **Service (`services/project_setup.py`)**:
    - Receives request.
    - Calls `utils/wizard.py` if interactive questions are needed.
    - Determines target path in `20-29_CODE`.

3.  **Adapter (`utils/templates.py`)**:
    - Loads `clean-arch` template.
    - Renders Jinja2 files with context variables.
    - Writes files to disk using `utils/filesystem.py` (Atomic Write).

4.  **Side Effect**:
    - `devbase ops track` is called internally to log the "Project Created" event.

---

## 🧪 Testing Strategy

We prioritize **Integration Tests** over Unit Tests for the CLI.

- **Tools**: `pytest`, `pytest-cov`
- **Pattern**: Invoke CLI commands against a temporary directory.
- **Coverage Goal**: >80% for `commands/` and `services/`.

```bash
# Run tests
uv run pytest
```
