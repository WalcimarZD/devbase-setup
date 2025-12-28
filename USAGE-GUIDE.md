# DevBase v5.0.0 - Field Manual (Usage Guide)

This guide provides a comprehensive reference for all `devbase` commands, workflows, and customization options. It is designed for developers who want to master their personal engineering operating system.

---

## 🛠️ Core Concepts

### Global Options
These flags work with **all** commands:

- `--root <path>`: Manually specify the workspace root (overrides auto-detection).
- `--verbose (-v)`: Enable detailed debug logs (useful for troubleshooting).
- `--no-color`: Disable rich terminal output (useful for CI/CD logs).
- `--version (-V)`: Display current DevBase version.

### Workspace Detection
DevBase v5.0.0 automatically finds your workspace root by walking up the directory tree looking for `.devbase_state.json`. You can run commands from *anywhere* inside your projects.

---

## 🟢 Essentials Group (Start Here)

### `devbase core`
*Manage the health and structure of your workspace.*

#### `core setup`
Initializes a new workspace or re-runs the configuration wizard.
```bash
devbase core setup
# Interactive mode (default)
devbase core setup --interactive
```
**What it does:**
1. Creates Johnny.Decimal folder structure.
2. Generates governance files (ADR templates, READMEs).
3. Configures git user and preferences.

#### `core doctor`
Diagnoses workspace issues and offers fixes.
```bash
# Check health
devbase core doctor

# Auto-fix standard issues (missing folders, broken symlinks)
devbase core doctor --fix
```

#### `core hydrate`
Updates workspace templates from the DevBase source without touching your data.
```bash
devbase core hydrate
```

### `devbase dev`
*Create and manage code projects.*

#### `dev new`
The primary command for starting work. Features a wizard for selecting templates.
```bash
# Interactive creation
devbase dev new my-new-project

# Bypass wizard (Golden Path)
devbase dev new my-api --template clean-arch --no-interactive

# Skip full setup (git init, install deps) for bare files
devbase dev new my-script --no-setup
```
**Templates:**
- `clean-arch`: Production-ready API structure.
- `python-lib`: Shared library/package.
- `script`: Minimal script scaffold.

#### `dev audit`
Enforces structure and naming conventions (kebab-case).
```bash
devbase dev audit
# Auto-rename violators (use with caution!)
devbase dev audit --fix
```

### `devbase nav`
*Navigate quickly.*

#### `nav goto`
Jumps to semantic locations. Designed for shell aliases.
```bash
devbase nav goto code      # Prints path to 20-29_CODE
devbase nav goto knowledge # Prints path to 10-19_KNOWLEDGE
```
**Pro Tip:** Add this function to your shell profile (.bashrc/.zshrc):
```bash
goto() { cd "$(devbase nav goto "$1")"; }
```

---

## 🟡 Daily Workflow Group

### `devbase ops`
*Operational excellence and tracking.*

#### `ops track`
Logs activity to your local telemetry database. Context-aware.
```bash
# In a project folder: logs as current project
cd my-api
devbase ops track "Refactored login handler"

# Explicit tracking
devbase ops track "Staff meeting" --type meeting
```

#### `ops stats`
Displays your productivity dashboard in the terminal.
```bash
devbase ops stats
```

#### `ops weekly`
Generates a Markdown report of your week's achievements.
```bash
# Generate report
devbase ops weekly --output week-42.md
```

#### `ops backup`
Creates an incremental backup of essential data (ignoring `node_modules`, `.venv`, etc.).
```bash
devbase ops backup
```

### `devbase quick`
*High-speed macros.*

#### `quick note`
Instantly captures a thought or TIL (Today I Learned).
```bash
# Quick capture
devbase quick note "Use --dry-run to test CLI commands safely"

# Open in VS Code immediately
devbase quick note "Complex architecture idea" --edit
```

#### `quick sync`
The "Monday Morning" command. Runs Doctor, Hydrate, and Backup in sequence.
```bash
devbase quick sync
```

---

## 🔵 Advanced Group (Power Users)

### `devbase pkm`
*Personal Knowledge Management graph tools.*

#### `pkm find`
Fast, full-text search across your markdown notes.
```bash
devbase pkm find "python async"
```

#### `pkm links`
Visualizes the forward and backward connections of a specific note.
```bash
devbase pkm links til/2025-12-22-typer.md
```

#### `pkm graph`
Displays network statistics and hub identification.
```bash
devbase pkm graph
# Generate HTML visualization
devbase pkm graph --html
```

### `devbase ai`
*AI-powered workspace intelligence.*

#### `ai config`
Configures the LLM provider (Groq) for AI features.
```bash
devbase ai config
# Prompts for API key and saves to ~/.devbase/config.toml
```

#### `ai organize`
Suggests the best Johnny.Decimal location for a file.
```bash
devbase ai organize inbox/random-notes.md
# Analyzes content and suggests destination with reasoning
```

#### `ai insights`
Analyzes your workspace structure for optimization opportunities.
```bash
devbase ai insights
# Generates a report on architecture, organization, and potential improvements
```

---

## 🎨 Template Customization

DevBase uses **Jinja2** for templating. You can customize the default templates found in `src/devbase/templates`.

### Structure
```
templates/
├── common/        # Shared partials (LICENSE, .gitignore)
├── clean-arch/    # Full project template
└── python-lib/    # Library template
```

### Variables
You can use standard DevBase variables in your custom templates:
- `{{ project_name }}`: "my-project"
- `{{ project_slug }}`: "my_project"
- `{{ author_name }}`: Configured git user
- `{{ year }}`: Current year

### Extending
To create a local custom template:
1. Copy an existing template folder in `src/devbase/templates`.
2. Modify `copier.yml` (if using Copier) or the Jinja2 files.
3. Use it via `--template my-custom-template`.
