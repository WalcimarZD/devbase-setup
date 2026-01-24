## 2025-05-23 - Status Spinners for Async Operations
**Learning:** Users often perceive CLI apps as "stuck" during long-running subprocess calls (like `npm install` or `uv sync`) if there's no visual movement. Static messages like "Installing..." aren't enough reassurance for operations that can take minutes.
**Action:** Use `rich.console.status` context manager to wrap any blocking `subprocess.run` calls. This provides an animated spinner that reassures the user the process is active, without needing complex threading or progress bars for indeterminate tasks.
## 2025-12-29 - [PKM New Interactive Prompt]
**Learning:** Adding interactive prompts () for missing optional arguments significantly improves CLI usability, preventing hard failures and guiding users (especially beginners) through required inputs. It turns a usage error into a guided workflow.
**Action:** Identify other required arguments in CLI commands that could benefit from a similar "prompt-if-missing" pattern to reduce friction.
## 2025-12-30 - [Dev New Interactive Prompt]
**Learning:** Typer's default behavior for missing arguments is to show an error and exit. By making the argument `Optional` and defaulting to `None`, we can check for its absence and provide an interactive prompt (via `rich.prompt.Prompt`). This improves the experience for new users who might not know the required arguments.
**Action:** Apply this pattern to other creation commands like `devbase docs new` or `devbase dev blueprint` to make them more discoverable and user-friendly.

## 2025-12-31 - [Structured Search Results]
**Learning:** Sequential printing of search results with metadata creates visual noise and makes scanning difficult. Users struggle to distinguish between entries when headers and metadata are interspersed vertically.
**Action:** Use `rich.Table` for structured data like search results. It enforces alignment, allowing users to scan columns (e.g., just the titles or just the types) efficiently, even in a CLI environment.
