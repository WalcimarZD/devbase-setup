## 2025-05-23 - Status Spinners for Async Operations
**Learning:** Users often perceive CLI apps as "stuck" during long-running subprocess calls (like `npm install` or `uv sync`) if there's no visual movement. Static messages like "Installing..." aren't enough reassurance for operations that can take minutes.
**Action:** Use `rich.console.status` context manager to wrap any blocking `subprocess.run` calls. This provides an animated spinner that reassures the user the process is active, without needing complex threading or progress bars for indeterminate tasks.
