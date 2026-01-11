# Sentinel's Journal

## 2025-02-23 - Path Traversal in Project Import
**Vulnerability:** The `import` command allowed path traversal characters (`..`) in the project name, which were directly used to construct the destination path for `git clone`. This could allow an attacker to overwrite files outside the project directory (e.g., `../../etc/passwd`).
**Learning:** Even with `pathlib`, simply joining paths with user input (e.g. `root / input`) is unsafe if the input contains `..` and isn't validated. While `resolve().relative_to()` is a good check, it's better to sanitize the input itself to be a safe filename first.
**Prevention:**
1.  Implemented `sanitize_filename` in `src/devbase/utils/security.py` to enforce safe characters (`[a-z0-9._-]`) and strip traversal sequences.
2.  Applied this sanitizer to all user-provided names in `development.py` (`new`, `import`, `worktree-add`).
3.  Added `validate_project_name` for strict checking when creating new projects.
