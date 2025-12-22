# ⚠️ DEPRECATED CODE - DO NOT MODIFY

**Status:** 🔴 SUNSET  
**Removal Target:** v5.0.0  
**Migration Guide:** See [MIGRATION.md](/docs/MIGRATION.md)

---

## Contents

| File | Replacement | Status |
|------|-------------|--------|
| `filesystem.py` | `adapters/filesystem_adapter.py` | 🟡 ACL Ready |
| `state.py` | `adapters/state_adapter.py` | 🟡 ACL Ready |
| `setup_core.py` | `adapters/setup_adapter.py` | 🟡 ACL Ready |
| `setup_code.py` | `adapters/setup_adapter.py` | 🟡 ACL Ready |
| `setup_ai.py` | `adapters/setup_adapter.py` | 🟡 ACL Ready |
| `setup_operations.py` | `adapters/setup_adapter.py` | 🟡 ACL Ready |
| `setup_pkm.py` | `adapters/setup_adapter.py` | 🟡 ACL Ready |
| `knowledge/database.py` | `adapters/knowledge_adapter.py` | 🟡 ACL Ready |
| `knowledge/graph.py` | `adapters/knowledge_adapter.py` | 🟡 ACL Ready |

---

## Rules for This Directory

1. **DO NOT** add new code to this directory
2. **DO NOT** add new imports from `devbase._deprecated` directly
3. Use adapters: `from devbase.adapters.* import get_*`
4. All changes require migration plan approval

---

## Feature Flags

Control legacy vs modern routing via `~/.devbase/config.toml`:

```toml
[migration]
use_legacy_filesystem = true  # Set to false when modern is ready
use_legacy_state = true
log_legacy_calls = true       # Log warnings on legacy calls
```

---

## History

- **2024-12-22**: Renamed from `legacy/` to `_deprecated/`
- **2024-12-22**: ACL adapters created in `adapters/`
- **TBD**: Complete migration to modern implementations
- **v5.0.0**: Target removal date
