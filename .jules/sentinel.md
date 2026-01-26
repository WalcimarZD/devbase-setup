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

## 2025-05-24 - Broken .gitignore Logic in Security Scanner
**Vulnerability:** The security scanner's `find_unprotected_secrets` function contained a logic error where `any(git_pat in gitignore_patterns ...)` always evaluated to True if `.gitignore` existed. This caused the scanner to report *zero* findings, creating a false sense of security.
**Learning:** Tautological conditions in list comprehensions/generators (checking if an item from a set is in that set) are subtle bugs that can completely disable security controls.
**Prevention:** Always test negative cases (files that should *not* be ignored) in security tool unit tests. Use established libraries like `pathspec` or `fnmatch` correctly instead of custom, fragile logic.
