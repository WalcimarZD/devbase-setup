## 2025-05-23 - Status Spinners for Async Operations
**Learning:** Users often perceive CLI apps as "stuck" during long-running subprocess calls (like `npm install` or `uv sync`) if there's no visual movement. Static messages like "Installing..." aren't enough reassurance for operations that can take minutes.
**Action:** Use `rich.console.status` context manager to wrap any blocking `subprocess.run` calls. This provides an animated spinner that reassures the user the process is active, without needing complex threading or progress bars for indeterminate tasks.
## 2025-12-29 - [PKM New Interactive Prompt]
**Learning:** Adding interactive prompts () for missing optional arguments significantly improves CLI usability, preventing hard failures and guiding users (especially beginners) through required inputs. It turns a usage error into a guided workflow.
**Action:** Identify other required arguments in CLI commands that could benefit from a similar "prompt-if-missing" pattern to reduce friction.
## 2025-12-29 - [PKM New Interactive Prompt]
**Learning:** Adding interactive prompts for missing optional arguments significantly improves CLI usability, preventing hard failures and guiding users (especially beginners) through required inputs. It turns a usage error into a guided workflow.
**Action:** Identify other required arguments in CLI commands that could benefit from a similar 'prompt-if-missing' pattern to reduce friction.
