# 🔧 How to Configure Git Hooks

Git hooks in DevBase validate your commits and enforce quality standards.

## Quick Setup

If hooks aren't installed yet:

```bash
devbase setup
```

This automatically configures `core.hooksPath` to `00-09_SYSTEM/06_git_hooks/`.

## Available Hooks

| Hook | Purpose |
|------|---------|
| `pre-commit` | Runs linters, checks for secrets |
| `commit-msg` | Validates commit message format |
| `pre-push` | Runs tests before push |

## Commit Message Format

DevBase enforces [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Examples

```bash
# Good
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(api): handle null response"
git commit -m "docs: update README"

# Bad (will be rejected)
git commit -m "fixed stuff"
git commit -m "WIP"
```

## Skipping Hooks (Emergency Only)

```bash
git commit --no-verify -m "hotfix: emergency patch"
```

> ⚠️ Use sparingly! Hooks exist to protect code quality.

## Customizing Hooks

Edit templates in:
```
shared/templates/hooks/
```

Then run `devbase hydrate` to apply changes.

---

**Related:**
- [First Project Tutorial](../tutorials/first-project.md)
- [Git Patterns Reference](../reference/git-patterns.md)
