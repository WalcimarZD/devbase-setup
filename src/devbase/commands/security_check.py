"""
Security Check Module
======================
Scans workspace for common security misconfigurations and exposed secrets.
"""
import fnmatch
import os
from pathlib import Path
from typing import List, Set, Tuple

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
    for current_root, dirs, _ in os.walk(root):
        # Prune ignored directories (Performance Win)
        # Modify dirs list in-place to prevent os.walk from visiting them
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        # Scan for sensitive patterns
        for pattern in SENSITIVE_FILE_PATTERNS:
            for file in Path(current_root).glob(pattern):
                if file.is_file():
                    # Check if explicitly ignored
                    try:
                        relative = str(file.relative_to(root)).replace("\\", "/")
                        is_ignored = False
                        for git_pat in gitignore_patterns:
                            # 1. Exact or glob match against relative path (e.g. "secret/*.key")
                            if fnmatch.fnmatch(relative, git_pat):
                                is_ignored = True
                                break

                            # 2. Match against filename only if pattern has no slash (e.g. "*.env")
                            if "/" not in git_pat and fnmatch.fnmatch(file.name, git_pat):
                                is_ignored = True
                                break

                            # 3. Match against directory prefix (e.g. "node_modules/")
                            if git_pat.endswith("/") and relative.startswith(git_pat):
                                is_ignored = True
                                break

                            # 4. Handle patterns without trailing slash that match directories (e.g. "build")
                            if relative.startswith(git_pat + "/"):
                                is_ignored = True
                                break

                        if not is_ignored:
                            issues.append((file, f"Unprotected secret file matches pattern: {pattern}"))
                    except ValueError:
                        # Path relative_to can fail if outside root (shouldn't happen with os.walk inside root)
                        pass

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
