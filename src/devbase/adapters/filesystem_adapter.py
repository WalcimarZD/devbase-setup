"""
FileSystem Anti-Corruption Layer Adapter
=========================================
Factory function that routes to legacy or modern FileSystem implementation
based on configuration flags.

This adapter isolates modern code from legacy implementation details.
When the new implementation is ready, only THIS file changes.

USAGE:
    from devbase.adapters.filesystem_adapter import get_filesystem
    
    fs = get_filesystem("/path/to/workspace")
    fs.ensure_dir("10-19_KNOWLEDGE/11_public_garden")
    fs.write_atomic("README.md", "# Hello World")
"""
from pathlib import Path
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from devbase._deprecated.filesystem import FileSystem


class IFileSystem(Protocol):
    """
    Interface contract for filesystem operations.
    
    All implementations (legacy and modern) must satisfy this protocol.
    This enables type-safe polymorphism without inheritance coupling.
    """
    
    root: Path
    
    def ensure_dir(self, path: str) -> Path:
        """Create directory idempotently and safely."""
        ...
    
    def write_atomic(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write file using atomic write-replace pattern."""
        ...
    
    def assert_safe_path(self, target_path: Path) -> bool:
        """Validate path is within root (prevents path traversal)."""
        ...
    
    def copy_atomic(self, source_path: str, dest_path: str) -> None:
        """Copy file atomically (copy-to-temp-then-rename)."""
        ...


def get_filesystem(root_path: str, dry_run: bool = False) -> IFileSystem:
    """
    Factory function that returns the appropriate FileSystem implementation.
    
    This is the ONLY entry point for filesystem operations.
    Modern code MUST NOT import from _deprecated directly.
    
    Args:
        root_path: Path to workspace root directory
        dry_run: If True, operations are logged but not executed
        
    Returns:
        IFileSystem: Implementation based on config flags
        
    Example:
        >>> fs = get_filesystem("~/Dev_Workspace")
        >>> fs.ensure_dir("00-09_SYSTEM/00_inbox")
    """
    from devbase.utils.config import get_config
    
    config = get_config()
    use_legacy = config.get("migration.use_legacy_filesystem", True)
    log_calls = config.get("migration.log_legacy_calls", False)
    
    if use_legacy:
        # DEPRECATED: Will be removed in v5.0.0
        from devbase._deprecated.filesystem import FileSystem
        
        if log_calls:
            import logging
            logger = logging.getLogger("devbase.deprecated")
            logger.warning(
                "DEPRECATED: Using legacy FileSystem. "
                "Set migration.use_legacy_filesystem=false to use modern implementation."
            )
        
        return FileSystem(root_path, dry_run)
    else:
        # TODO: Implement modern FileSystem when ready
        # For now, fall back to legacy with warning
        import warnings
        warnings.warn(
            "Modern FileSystem not yet implemented. Falling back to legacy.",
            FutureWarning,
            stacklevel=2
        )
        from devbase._deprecated.filesystem import FileSystem
        return FileSystem(root_path, dry_run)
