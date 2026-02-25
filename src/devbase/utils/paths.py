"""
Path Resolution Utilities
=========================
Ensures all DevBase file operations default to workspace-relative paths.
"""
from pathlib import Path


def resolve_workspace_path(
    output: Path,
    root: Path,
    default_subdir: str = ""
) -> Path:
    """
    Resolve output paths relative to workspace root.
    
    DevBase philosophy: All generated files belong inside the workspace
    unless the user explicitly provides an absolute path to "escape".
    
    Args:
        output: User-provided output path (may be relative or absolute)
        root: Workspace root directory
        default_subdir: Default subdirectory within workspace (e.g., "10-19_KNOWLEDGE/...")
        
    Returns:
        Path: Resolved absolute path
        
    Examples:
        >>> resolve_workspace_path(Path("report.md"), Path("D:/Dev_OS"), "10-19_KNOWLEDGE")
        Path("D:/Dev_OS/10-19_KNOWLEDGE/report.md")
        
        >>> resolve_workspace_path(Path("C:/Temp/report.md"), Path("D:/Dev_OS"), "10-19_KNOWLEDGE")
        Path("C:/Temp/report.md")  # Absolute path escapes workspace
    """
    if output.is_absolute():
        return output
    
    if default_subdir:
        return root / default_subdir / output
    return root / output


# =============================================================================
# Johnny.Decimal Path Registry
# =============================================================================

JD_SYSTEM = "00-09_SYSTEM"
JD_KNOWLEDGE = "10-19_KNOWLEDGE"
JD_CODE = "20-29_CODE"
JD_OPERATIONS = "30-39_OPERATIONS"
JD_MEDIA = "40-49_MEDIA_ASSETS"
JD_ARCHIVE = "90-99_ARCHIVE_COLD"

JD_PLANNING = f"{JD_SYSTEM}/02_planning"
JD_TEMPLATES = f"{JD_SYSTEM}/05_templates"
JD_REFERENCES = f"{JD_KNOWLEDGE}/10_references"
JD_PUBLIC_GARDEN = f"{JD_KNOWLEDGE}/11_public_garden"
JD_PRIVATE_VAULT = f"{JD_KNOWLEDGE}/12_private-vault"
JD_JOURNAL = f"{JD_PRIVATE_VAULT}/journal"


# =============================================================================
# DevBase Directory Resolution (Portable Workspace Support)
# =============================================================================

from typing import Optional


def get_devbase_dir(root: Optional[Path] = None) -> Path:
    """
    Get the .devbase directory path.
    
    Resolution order:
    1. Workspace-local: <root>/.devbase (if root provided and on different drive)
    2. Global fallback: ~/.devbase
    
    Args:
        root: Workspace root path (optional)
        
    Returns:
        Path to .devbase directory
    """
    if root:
        local_dir = root / ".devbase"
        if local_dir.exists() or _should_prefer_local(root):
            return local_dir
    return Path.home() / ".devbase"


def get_config_path(root: Optional[Path] = None) -> Path:
    """Get path to config.toml file."""
    return get_devbase_dir(root) / "config.toml"


def get_db_path(root: Optional[Path] = None) -> Path:
    """Get path to DuckDB database file."""
    return get_devbase_dir(root) / "devbase.duckdb"


def get_bin_dir(root: Optional[Path] = None) -> Path:
    """Get path to binaries directory (nuget.exe, etc)."""
    return get_devbase_dir(root) / "bin"


def get_icons_dir(root: Optional[Path] = None) -> Path:
    """Get path to icons directory."""
    return get_devbase_dir(root) / "icons"


def get_tools_dir(root: Optional[Path] = None) -> Path:
    """Get path to tools directory (UV tools, etc)."""
    return get_devbase_dir(root) / "tools"


def _should_prefer_local(root: Path) -> bool:
    """
    Determine if we should prefer local workspace storage.
    
    Returns True if:
    - Root is on a different drive than home (e.g., D: vs C:)
    - Root/.devbase already has some content
    """
    try:
        home_drive = Path.home().drive.upper()
        root_drive = root.drive.upper()
        return home_drive != root_drive
    except Exception:
        return False


def ensure_devbase_dir(root: Optional[Path] = None) -> Path:
    """Get .devbase directory, creating it if needed."""
    devbase_dir = get_devbase_dir(root)
    devbase_dir.mkdir(parents=True, exist_ok=True)
    return devbase_dir
