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

#### `core hydrate-icons`
Updates workspace folder icons (requires custom icons in `~/.devbase/icons`).
```bash
devbase core hydrate-icons
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

#### `dev import`
Import an existing project (brownfield) into the workspace.
```bash
# Clone from Git
devbase dev import https://github.com/user/repo.git

# Clone and restore NuGet packages (.NET)
devbase dev import https://github.com/user/dotnet-app.git --restore

# Import local project
devbase dev import D:\Projects\legacy-app --name legacy
```
Imported projects are marked as "external" and exempt from governance rules.

#### `dev list`
List all projects in the workspace with governance status.
```bash
devbase dev list
```
Shows: Project name, last modified, governance level (Full/External/Worktree).

#### `dev info`
Show detailed metadata for a project.
```bash
devbase dev info my-project
```
Displays: Template used, creation date, author, governance level.

#### `dev open`
Open a project in VS Code.
```bash
devbase dev open my-project
```

#### `dev restore`
Restore NuGet packages for .NET Framework projects.
```bash
devbase dev restore MedSempreMVC_GIT
devbase dev restore MyProject --solution MyProject.Web.sln
```
Downloads `nuget.exe` automatically if not present.

#### `dev archive`
Archive a project to `90-99_ARCHIVE_COLD`.
```bash
devbase dev archive my-project
```

#### `dev update`
Update a project from its template (using Copier).
```bash
devbase dev update my-project
```

#### `dev blueprint`
Generate project file structure using AI based on a description.
```bash
devbase dev blueprint "A FastAPi service with Celery"
```

#### `dev adr-gen`
Generate an Architecture Decision Record (ADR) draft based on telemetry events.
```bash
devbase dev adr-gen
```

#### `dev audit`
Enforces structure and naming conventions (kebab-case).
```bash
devbase dev audit
# Auto-rename violators (use with caution!)
devbase dev audit --fix
```

#### Worktree Commands
Manage git worktrees for parallel development.
```bash
# Create a worktree
devbase dev worktree-add my-project feature/new-feature
devbase dev worktree-add my-project hotfix/bug-123 --create  # Create new branch

# List all worktrees
devbase dev worktree-list
devbase dev worktree-list my-project  # For specific project

# Remove a worktree
devbase dev worktree-remove my-project--feature-new-feature
```
Worktrees are stored in `22_worktrees/` and shown in `dev list` with `[Worktree]` badge.

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

#### `ops clean`
Clean up temporary files and caches.
```bash
devbase ops clean
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

#### `quick quickstart`
Runs the Getting Started tutorial.
```bash
devbase quick quickstart
```

### `devbase docs`
*Documentation management.*

#### `docs new`
Create a new documentation file.
```bash
devbase docs new
```

---

## 🔵 Advanced Group (Power Users)

### `devbase pkm`
*Personal Knowledge Management graph tools.*

#### `pkm new`
Create a new note with Diataxis structure.
```bash
devbase pkm new --type tutorial "How to use DuckDB"
```

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

#### `pkm index`
Manually re-index the knowledge base.
```bash
devbase pkm index
```

### `devbase study`
*Learning and spaced repetition.*

#### `study review`
Review flashcards or notes.
```bash
devbase study review
```

#### `study synthesize`
Synthesize notes into a summary.
```bash
devbase study synthesize
```

### `devbase analytics`
*Advanced productivity insights.*

#### `analytics report`
Generate a comprehensive productivity report.
```bash
devbase analytics report
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

#### `ai chat`
Interactive chat with your workspace using Local RAG (Retrieval-Augmented Generation).
```bash
devbase ai chat "Como eu implemento um adaptador de armazenamento no DevBase?"
# Busca contexto no seu workspace e responde via IA
```

#### `ai index`
Rebuilds the semantic search index for your local files.
```bash
devbase ai index --rebuild
```

#### `ai classify`
Classify content using AI.
```bash
devbase ai classify <path>
```

#### `ai summarize`
Summarize content using AI.
```bash
devbase ai summarize <path>
```

#### `ai insights`
Generate insights from your data.
```bash
devbase ai insights
```

#### `ai status`
Check the status of AI services.
```bash
devbase ai status
```

#### `ai routine`
*Cognitive assistance and daily hygiene.*

- `briefing`: Shows pending tasks and activity summary.
- `triage`: Interactive organization of your `00_inbox`.

```bash
devbase ai routine briefing
devbase ai routine triage --apply
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


## Undocumented Commands (Auto-detected)
- `devbase ai classify`
- `devbase ai summarize`


## Undocumented Commands/Flags (Auto-detected)
- `pkm journal (command)`
- `pkm icebox (command)`
- `audit run --days`
