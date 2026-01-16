## 2025-05-23 - Status Spinners for Async Operations
**Learning:** Users often perceive CLI apps as "stuck" during long-running subprocess calls (like `npm install` or `uv sync`) if there's no visual movement. Static messages like "Installing..." aren't enough reassurance for operations that can take minutes.
**Action:** Use `rich.console.status` context manager to wrap any blocking `subprocess.run` calls. This provides an animated spinner that reassures the user the process is active, without needing complex threading or progress bars for indeterminate tasks.
## 2025-12-29 - [PKM New Interactive Prompt]
**Learning:** Adding interactive prompts () for missing optional arguments significantly improves CLI usability, preventing hard failures and guiding users (especially beginners) through required inputs. It turns a usage error into a guided workflow.
**Action:** Identify other required arguments in CLI commands that could benefit from a similar "prompt-if-missing" pattern to reduce friction.
## 2025-12-30 - [Dev New Interactive Prompt]
**Learning:** Typer's default behavior for missing arguments is to show an error and exit. By making the argument `Optional` and defaulting to `None`, we can check for its absence and provide an interactive prompt (via `rich.prompt.Prompt`). This improves the experience for new users who might not know the required arguments.
**Action:** Apply this pattern to other creation commands like `devbase docs new` or `devbase dev blueprint` to make them more discoverable and user-friendly.
## 2025-12-31 - [Rich Text Highlighting]
**Learning:** Highlighting search terms in CLI output is tricky when using markup parsers (like `rich`) because escaping content can interfere with formatting tags. Specifically, backslashes in user content can escape subsequent tags if not handled carefully.
**Action:** Use `rich.text.Text` object and its `.highlight_regex()` method instead of constructing markup strings manually. This separates content from styling, preventing injection issues and rendering bugs with special characters.
