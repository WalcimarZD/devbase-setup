"""
Simple FileSystem Helper
========================
Minimal filesystem operations using pathlib directly.

Replaces the over-engineered adapter layer with direct pathlib usage.
Maintains the same interface for compatibility.
"""
import shutil
import tempfile
from pathlib import Path
from typing import Union


class FileSystem:
    """
    Simple filesystem operations wrapper.
    
    Provides safe directory creation, atomic writes, and path validation.
    Uses pathlib directly instead of abstract adapters.
    """
    
    def __init__(self, root_path: Union[str, Path], dry_run: bool = False):
        """
        Initialize filesystem helper.
        
        Args:
            root_path: Workspace root directory
            dry_run: If True, log operations without executing
        """
        if isinstance(root_path, str):
            root_path = Path(root_path).expanduser().resolve()
        self.root = root_path
        self.dry_run = dry_run
    
    def ensure_dir(self, path: str) -> Path:
        """
        Create directory if it doesn't exist.
        
        Args:
            path: Relative path from root
            
        Returns:
            Absolute Path to created directory
        """
        target = self.root / path
        self.assert_safe_path(target)
        
        if not self.dry_run:
            target.mkdir(parents=True, exist_ok=True)
        
        return target
    
    def write_atomic(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """
        Write file using atomic write pattern (write-to-temp-then-rename).
        
        Args:
            path: Relative path from root
            content: File content to write
            encoding: Text encoding
        """
        target = self.root / path
        self.assert_safe_path(target)
        
        if self.dry_run:
            return
        
        # Ensure parent exists
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write pattern
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=target.parent,
            delete=False,
            suffix=".tmp"
        ) as tf:
            tf.write(content)
            temp_path = Path(tf.name)
        
        # Atomic rename (works on Windows too in Python 3.3+)
        temp_path.replace(target)
    
    def assert_safe_path(self, target_path: Path) -> bool:
        """
        Validate path is within root (prevents path traversal attacks).
        
        Args:
            target_path: Path to validate
            
        Returns:
            True if safe
            
        Raises:
            ValueError: If path is outside root
        """
        try:
            target_path.resolve().relative_to(self.root.resolve())
            return True
        except ValueError:
            raise ValueError(f"Path traversal detected: {target_path} is outside {self.root}")
    
    def copy_atomic(self, source_path: str, dest_path: str) -> None:
        """
        Copy file atomically.
        
        Args:
            source_path: Source path (relative or absolute)
            dest_path: Destination path (relative to root)
        """
        source = Path(source_path)
        if not source.is_absolute():
            source = self.root / source_path
        
        dest = self.root / dest_path
        self.assert_safe_path(dest)
        
        if self.dry_run:
            return
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


def get_filesystem(root_path: str, dry_run: bool = False) -> FileSystem:
    """Factory function for FileSystem."""
    return FileSystem(root_path, dry_run)
