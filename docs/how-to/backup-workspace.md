# 💾 How to Backup Your Workspace

DevBase uses the **3-2-1 backup strategy**: 3 copies, 2 media types, 1 offsite.

## Quick Backup

```bash
devbase backup
```

This creates a timestamped backup at:
```
30-39_OPERATIONS/31_backups/local/devbase_backup_YYYYMMDD_HHMMSS/
```

## The 3-2-1 Strategy

| Copy | Location | Type |
|------|----------|------|
| **1** | Original workspace | Primary |
| **2** | Local backup | Same drive |
| **3** | External drive | External media |
| **3** | Cloud sync | Offsite |

## Excluding the Private Vault

By default, backups **exclude** `12_private_vault/` for security.

To include it (for local backups only):

```bash
devbase backup --include-vault
```

> ⚠️ Never sync vault to cloud!

## Automated Backups

### Windows Task Scheduler

```powershell
schtasks /create /tn "DevBase Backup" /tr "python devbase.py backup" /sc weekly /d SUN /st 02:00
```

### Linux/macOS Cron

```bash
# Add to crontab -e
0 2 * * 0 cd ~/Dev_Workspace && python devbase.py backup
```

## Restoring from Backup

1. Locate your backup in `31_backups/local/`
2. Copy contents to your workspace root
3. Run `devbase doctor` to verify

---

**Related:**
- [Air-Gap Security](../explanation/air-gap-security.md)
- [Backup Command Reference](../reference/cli-commands.md#backup)
