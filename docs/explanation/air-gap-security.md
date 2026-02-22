# 🔒 Understanding Air-Gap Security

The **Private Vault** in DevBase is protected by "Air-Gap Security".

## What is Air-Gap?

An **air gap** is a network security measure where a system is physically isolated from unsecured networks.

In DevBase, we apply this concept to your **most sensitive data**.

## The Private Vault

Located at:
```
10-19_KNOWLEDGE/12_private_vault/
```

This folder contains:
- Personal journal entries
- Brag documents (career achievements)
- Private notes and reflections
- Sensitive research

## How It's Protected

### 1. Git Ignore

The vault is **always** excluded from Git:

```gitignore
# .gitignore
12_private_vault/
```

> ⚠️ This line is added automatically by `devbase setup`

### 2. No Cloud Sync

When using cloud sync tools (Dropbox, OneDrive, Google Drive), **exclude this folder**.

### 3. Backup Separation

When running `devbase backup`, the vault is backed up **separately** to a local-only location.

## Why This Matters

| Concern | Protection |
|---------|------------|
| **Accidental commit** | Git ignores the folder |
| **Cloud leak** | Never syncs to cloud |
| **Employer access** | Stays on your machine |

## Setting Up Additional Protection

For extra security, consider:

1. **Encryption**: Use VeraCrypt or BitLocker
2. **Separate drive**: Store on encrypted USB
3. **Local backup**: Schedule encrypted backups

---

> "Not everything needs to be in the cloud."
