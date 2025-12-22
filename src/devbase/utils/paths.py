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
