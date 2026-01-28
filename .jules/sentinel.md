## 2024-05-23 - Argument Injection in Git Commands
**Vulnerability:** User input passed directly to `git clone` as a source argument allowed passing options to git (e.g., `-u` for upload-pack).
**Learning:** Even when `subprocess.run` uses a list of arguments, git interprets arguments starting with `-` as options unless preceded by `--`. This is a common pattern in CLI tools.
**Prevention:** Always use `--` delimiter when passing user input to CLI tools that support it (like git, grep, etc.). Example: `git clone -- <source> <dest>`.
## 2024-05-24 - Argument Injection in Git Worktree
**Vulnerability:** Argument injection was possible in `git worktree add` where a branch name starting with `-` (e.g., `--help`) could be interpreted as a git option, potentially causing unexpected behavior or denial of service (showing help instead of executing).
**Learning:** The previous fix for `git clone` was not applied consistently across all git operations. Subcommands like `worktree add` are equally vulnerable.
**Prevention:** Audit all `subprocess.run` calls involving external CLIs (especially git) and ensure the `--` delimiter is used before any variable arguments (paths, branch names, etc.).

## 2025-01-02 - Unconfirmed Shell Execution in Project Setup
**Vulnerability:** `ProjectSetupService` executed package manager commands (`npm install`, `uv sync`, etc.) automatically when detecting configuration files. If a user was tricked into generating a project from a malicious template (Supply Chain Attack), this could trigger arbitrary code execution via `postinstall` scripts without explicit user consent.
**Learning:** Automation is convenient but dangerous when it involves executing untrusted code or scripts. "Golden Path" features should not sacrifice security for zero-friction.
**Prevention:** Always require user confirmation (interactive prompt) before executing commands that can run arbitrary code, especially in context of setup/installation scripts. Added `interactive` flag and `Confirm.ask` guard.

## 2026-01-28 - Command Injection in Editor Launch
**Vulnerability:** User input (file path) was passed to `subprocess.run(f"code {path}", shell=True)` allowing command injection if the path contained malicious characters (e.g. `; rm -rf /`).
**Learning:** Using `shell=True` with string formatting is almost always unsafe, even if the input seems partially controlled.
**Prevention:** Always use the list format `subprocess.run(["cmd", "arg"])` and avoid `shell=True`. This automatically handles escaping and prevents injection.
