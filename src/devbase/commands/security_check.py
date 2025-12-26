"""
Security Check Module
======================
Scans workspace for common security misconfigurations and exposed secrets.
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Tuple, Set

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

# Directories to always ignore during scan (Performance Optimization)
IGNORED_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "target",
    "vendor",
    "coverage",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
}

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
    
    Optimized to use os.walk with pruning of heavy directories.

    Returns:
        List of (file_path, reason) tuples
    """
    issues = []
    
    # Load .gitignore patterns
    gitignore_patterns: Set[str] = set()
    gitignore_path = root / ".gitignore"
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        gitignore_patterns.add(line)
        except Exception:
            # Fail safe if gitignore cannot be read
            pass

    # Walk the directory tree
    for current_root, dirs, files in os.walk(root):
        # Prune ignored directories (Performance Win)
        # Modify dirs list in-place to prevent os.walk from visiting them
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        # Additional pruning based on .gitignore (simple directory matches)
        # This skips scanning subtrees that are explicitly ignored by name
        dirs[:] = [
            d for d in dirs
            if d not in gitignore_patterns and f"{d}/" not in gitignore_patterns
        ]

        for filename in files:
            # Check if file matches any sensitive pattern
            matched_pattern = None
            for pattern in SENSITIVE_FILE_PATTERNS:
                if fnmatch.fnmatch(filename, pattern):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                continue

            # Found a candidate, now check if it is ignored
            file_path = Path(current_root) / filename
            relative_path = str(file_path.relative_to(root)).replace("\\", "/")

            is_ignored = False
            for gitignore_pat in gitignore_patterns:
                # 1. Directory prefix match (e.g., "secrets/" matches "secrets/key.pem")
                clean_pat = gitignore_pat.rstrip("/")
                if gitignore_pat.endswith("/") and (
                    relative_path == clean_pat or relative_path.startswith(f"{clean_pat}/")
                ):
                    is_ignored = True
                    break

                # 2. Exact match
                if relative_path == gitignore_pat:
                    is_ignored = True
                    break

                # 3. Glob match (e.g., "*.pem" matches "key.pem" or "subdir/key.pem")
                # gitignore patterns apply to basename if they contain no slash
                if "/" not in gitignore_pat:
                    if fnmatch.fnmatch(filename, gitignore_pat):
                        is_ignored = True
                        break
                else:
                    # Path-specific glob (e.g., "config/*.secret")
                    if fnmatch.fnmatch(relative_path, gitignore_pat):
                        is_ignored = True
                        break

            if not is_ignored:
                issues.append((file_path, f"Unprotected secret file matches pattern: {matched_pattern}"))
    
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
