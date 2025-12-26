"""
Security Check Module
======================
Scans workspace for common security misconfigurations and exposed secrets.
"""
import re
from pathlib import Path
from typing import List, Tuple

from rich.console import Console

console = Console()

# Patterns for sensitive files that should be in .gitignore
SENSITIVE_FILE_PATTERNS = [
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "*.pem",
    "*.key",
    "*id_rsa*",
    "*id_ed25519*",
    "*.p12",
    "*.pfx",
    ".pypirc",
    ".npmrc",
]

# Known cloud sync directories
CLOUD_SYNC_PATHS = [
    "OneDrive",
    "Dropbox",
    "Google Drive",
    "iCloud Drive",
]


def find_unprotected_secrets(root: Path) -> List[Tuple[Path, str]]:
    """
    Scan workspace for secret files not protected by .gitignore.
    
    Returns:
        List of (file_path, reason) tuples
    """
    issues = []
    
    # Load .gitignore if exists
    gitignore_path = root / ".gitignore"
    gitignore_patterns = set()
    
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    gitignore_patterns.add(line)
    
    # Scan for sensitive files
    for pattern in SENSITIVE_FILE_PATTERNS:
        # Convert glob to regex for checking
        pattern_clean = pattern.replace("*", "")
        
        # recursive glob pattern
        # If pattern starts with *, we want to match anywhere. rglob does this for filename matching in subdirs.
        # But rglob("*pattern") matches "pattern" in any subdirectory.

        for file in root.rglob(pattern):
            if file.is_file():
                # Check if explicitly ignored
                relative = str(file.relative_to(root)).replace("\\", "/")
                is_ignored = any(
                    pattern in gitignore_patterns 
                    or relative.startswith(pattern.rstrip("/"))
                    for pattern in gitignore_patterns
                )
                
                if not is_ignored:
                    issues.append((file, f"Unprotected secret file matches pattern: {pattern}"))
    
    return issues


def check_backup_contains_secrets(root: Path) -> List[str]:
    """
    Check if backup directory contains unencrypted secrets.
    
    Returns:
        List of warning messages
    """
    warnings = []
    backup_dir = root / "30-39_OPERATIONS" / "31_backups" / "local"
    
    if not backup_dir.exists():
        return warnings
    
    # Scan backups for sensitive files
    for pattern in [".env", "*.pem", "*.key"]:
        matches = list(backup_dir.rglob(pattern))
        if matches:
            warnings.append(
                f"Found {len(matches)} {pattern} file(s) in backups. "
                "Ensure backups are encrypted before cloud sync."
            )
    
    # Check if private vault is in backups
    for backup in backup_dir.iterdir():
        if backup.is_dir():
            vault_path = backup / "10-19_KNOWLEDGE" / "12_private_vault"
            if vault_path.exists():
                warnings.append(
                    f"Backup '{backup.name}' contains unencrypted private_vault. "
                    "This folder contains sensitive data."
                )
    
    return warnings


def check_vault_in_cloud_sync(root: Path) -> List[str]:
    """
    Detect if private_vault is inside a cloud-synced directory.
    
    Returns:
        List of warning messages
    """
    warnings = []
    vault_path = root / "10-19_KNOWLEDGE" / "12_private_vault"
    
    if not vault_path.exists():
        return warnings
    
    # Check if any parent is a known cloud sync folder
    vault_abs = vault_path.resolve()
    for cloud_name in CLOUD_SYNC_PATHS:
        if cloud_name in str(vault_abs):
            warnings.append(
                f"Private Vault detected inside '{cloud_name}' sync folder. "
                "This may expose sensitive data to cloud storage. "
                "Consider moving workspace outside cloud-synced directories or excluding 12_private_vault."
            )
            break
    
    return warnings


def run_security_checks(root: Path) -> bool:
    """
    Run all security checks and display results.
    
    Returns:
        True if all checks passed, False if issues found
    """
    all_clear = True
    
    console.print("\n[bold]Security Audit[/bold]")
    
    # Check 1: Unprotected secrets
    unprotected = find_unprotected_secrets(root)
    if unprotected:
        all_clear = False
        for file, reason in unprotected[:5]:  # Limit output
            console.print(f"  [red]✗[/red] {file.relative_to(root)}")
            console.print(f"    [dim]{reason}[/dim]")
        if len(unprotected) > 5:
            console.print(f"  [dim]... and {len(unprotected) - 5} more[/dim]")
        console.print("  [yellow]→ Add these files to .gitignore[/yellow]")
    else:
        console.print("  [green]✓[/green] No unprotected secrets found")
    
    # Check 2: Backups with secrets
    backup_warnings = check_backup_contains_secrets(root)
    if backup_warnings:
        all_clear = False
        for warning in backup_warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")
    else:
        console.print("  [green]✓[/green] Backups appear clean")
    
    # Check 3: Cloud sync
    cloud_warnings = check_vault_in_cloud_sync(root)
    if cloud_warnings:
        all_clear = False
        for warning in cloud_warnings:
            console.print(f"  [yellow]⚠[/yellow] {warning}")
    else:
        console.print("  [green]✓[/green] Private Vault not in known cloud sync paths")
    
    return all_clear
