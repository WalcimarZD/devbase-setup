# 📂 Understanding Johnny.Decimal

Johnny.Decimal is the organizational system at the heart of DevBase.

## The Problem

Most developers face:
- **Scattered files** across random folders
- **No standard structure** between projects
- **Difficulty finding** things later

## The Solution

Johnny.Decimal uses a **numbered hierarchy**:

```
XX-YY_CATEGORY/
└── ZZ_subcategory/
```

### DevBase Structure

| Range | Category | Purpose |
|-------|----------|---------|
| `00-09` | SYSTEM | Configuration, dotfiles, documentation |
| `10-19` | KNOWLEDGE | Notes, research, private vault |
| `20-29` | CODE | Projects, templates, worktrees |
| `30-39` | OPERATIONS | Automation, backups, credentials |
| `40-49` | MEDIA_ASSETS | Images, videos, designs |
| `90-99` | ARCHIVE_COLD | Completed/archived projects |

## Why Numbers?

1. **Predictable locations** - You always know where to look
2. **Sortable** - Numbers sort naturally
3. **Limited categories** - 10 max per level, forces organization
4. **Universal** - Works across any OS/tool

## Example

Looking for a project's database schema?

```
20-29_CODE/           # →  I know it's code-related
└── 21_monorepo_apps/ # → It's an active app
    └── my-project/   # → Found it!
        └── src/
            └── infrastructure/
                └── persistence/  # → Schema here
```

## Learn More

- [Original Johnny.Decimal](https://johnnydecimal.com/)
- [DevBase Structure Reference](../reference/structure.md)

---

> "A place for everything, and everything in its place."
