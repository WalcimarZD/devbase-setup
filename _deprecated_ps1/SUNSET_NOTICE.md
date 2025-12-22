# ⚠️ DEPRECATED POWERSHELL SCRIPTS - DO NOT MODIFY

**Status:** 🔴 SUNSET  
**Removal Target:** v5.0.0  
**Replaced By:** Python CLI (`devbase` command)

---

## Contents

| Script | Python Replacement | Status |
|--------|-------------------|--------|
| `bootstrap.ps1` | `devbase core setup` | 🟢 Replaced |
| `cli-functions.ps1` | `devbase.commands.*` | 🟢 Replaced |
| `common-functions.ps1` | `devbase._deprecated.filesystem` | 🟡 Migrating |
| `setup-ai.ps1` | `devbase core setup --ai` | 🟢 Replaced |
| `setup-code.ps1` | `devbase core setup --code` | 🟢 Replaced |
| `setup-core.ps1` | `devbase core setup` | 🟢 Replaced |
| `setup-hooks.ps1` | `devbase dev hooks` | 🟢 Replaced |
| `setup-operations.ps1` | `devbase ops backup` | 🟢 Replaced |
| `setup-pkm.ps1` | `devbase pkm *` | 🟢 Replaced |
| `setup-templates.ps1` | `devbase dev new` | 🟢 Replaced |

---

## Rules

1. **DO NOT** modify these scripts
2. **DO NOT** reference these scripts from new code
3. Use the Python CLI: `devbase --help`

---

## History

- **2024-12-22**: Moved from `modules/` to `_deprecated_ps1/`
- **v5.0.0**: Target deletion date
