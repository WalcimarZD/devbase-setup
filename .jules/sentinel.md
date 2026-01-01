## 2024-05-23 - Argument Injection in Git Commands
**Vulnerability:** User input passed directly to `git clone` as a source argument allowed passing options to git (e.g., `-u` for upload-pack).
**Learning:** Even when `subprocess.run` uses a list of arguments, git interprets arguments starting with `-` as options unless preceded by `--`. This is a common pattern in CLI tools.
**Prevention:** Always use `--` delimiter when passing user input to CLI tools that support it (like git, grep, etc.). Example: `git clone -- <source> <dest>`.
## 2024-05-24 - Argument Injection in Git Worktree
**Vulnerability:** Argument injection was possible in `git worktree add` where a branch name starting with `-` (e.g., `--help`) could be interpreted as a git option, potentially causing unexpected behavior or denial of service (showing help instead of executing).
**Learning:** The previous fix for `git clone` was not applied consistently across all git operations. Subcommands like `worktree add` are equally vulnerable.
**Prevention:** Audit all `subprocess.run` calls involving external CLIs (especially git) and ensure the `--` delimiter is used before any variable arguments (paths, branch names, etc.).
