# Migration Guide: Moving to DevBase v5.0.0

> [!WARNING]
> **PowerShell Decommissioned**: v5.0.0 removes all support for PowerShell runtimes (`bootstrap.ps1`, `profile.ps1`). The system now runs entirely on Python 3.13 via `uv`.

## 📦 Major Changes

### 1. Installation & Runtime
- **Old (v4)**: Relied on system Python + PowerShell scripts. Fragile dependency management.
- **New (v5)**: Uses `uv` to create a strictly isolated, high-performance environment.

### 2. Command Structure
The CLI has been reorganized into logical groups for better discoverability.

| Legacy (v4) | Modern (v5) |
| :--- | :--- |
| `python devbase.py doctor` | `devbase core doctor` |
| `devbase.py new <name>` | `devbase dev new <name>` |
| `devbase.py track <msg>` | `devbase ops track <msg>` |
| `devbase.py stats` | `devbase ops stats` |
| `devbase.py backup` | `devbase ops backup` |

### 3. Usage from Anywhere
- **Old (v4)**: Often required `cd ~/devbase-setup` or setting `--root` explicitly.
- **New (v5)**: Auto-detects workspace root from any subdirectory. Just type `devbase <cmd>`.

---

## 🛠️ Step-by-Step Migration

### Step 1: Uninstall Legacy Integations
If you added aliases to your shell profile (`.bashrc`, `.zshrc`, `Microsoft.PowerShell_profile.ps1`), remove them:

```bash
# REMOVE lines like this:
alias db="python ~/devbase-setup/devbase.py"
```

### Step 2: Install v5.0.0
Install the new global CLI tool:
```bash
uv tool install devbase
```
*Note: If you don't use `uv`, run the one-line installer:*
```bash
curl -Ls https://raw.githubusercontent.com/walcimarzd/devbase-setup/main/install.sh | bash
```

### Step 3: Verify Data
Your `Dev_Workspace` data **remains untouched**. v5.0.0 reads the existing `.devbase_state.json` file.

Run `doctor` to verify permissions and structure:
```bash
devbase core doctor
```

### Step 4: Update Aliases (Optional)
If you want short aliases, add these to your shell config:

```bash
# New v5 aliases
alias db="devbase"
alias nav="devbase nav goto"
```

---

## ❓ FAQ

**Q: Do I need to move my project files?**
A: No. DevBase v5 respects your existing Johnny.Decimal structure (e.g., `20-29_CODE`).

**Q: What happened to `bootstrap.ps1`?**
A: It was deleted. `devbase core setup` now handles all initialization logic with a richer, safer interactive wizard.

**Q: I have custom templates. Will they break?**
A: Most Jinja2 templates will work as-is. If you used custom PowerShell hooks in your templates, you will need to migrate them to Python or standard shell scripts.
