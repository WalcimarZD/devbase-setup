"""
Folder Icon System - Cross-Platform Implementation
===================================================
Applies custom icons to Johnny.Decimal folders based on Style Guide.

Supports:
- Windows (desktop.ini + folder attributes)
- macOS (via AppKit/PyObjC if available)
- Linux (gio metadata for GNOME)
"""
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Optional

from devbase.utils.paths import get_icons_dir as _get_icons_dir

from rich.console import Console

console = Console()

# Area color/theme mapping from Style Guide
AREA_ICONS: Dict[str, Dict] = {
    "00-09_SYSTEM": {
        "name": "System",
        "color": "#FF3B30",  # Red/Pulse
        "icon": "00.ico",
    },
    "10-19_KNOWLEDGE": {
        "name": "Knowledge",
        "color": "#007AFF",  # Deep Blue
        "icon": "10.ico",
    },
    "20-29_CODE": {
        "name": "Code",
        "color": "#30D158",  # Terminal Green
        "icon": "20.ico",
    },
    "30-39_OPERATIONS": {
        "name": "Operations",
        "color": "#BF5AF2",  # Purple/AI
        "icon": "30.ico",
    },
    "40-49_MEDIA_ASSETS": {
        "name": "Media",
        "color": "#FF9F0A",  # Orange
        "icon": "40.ico",
    },
    "90-99_ARCHIVE_COLD": {
        "name": "Archive",
        "color": "#8E8E93",  # Grey/Ice
        "icon": "90.ico",
    },
}


def get_icon_dir(root: Optional[Path] = None) -> Path:
    """Get the directory where icons are stored (workspace-local or global)."""
    return _get_icons_dir(root)


def set_icon_windows(folder_path: Path, icon_path: Path) -> bool:
    """
    Set custom icon for a folder on Windows using desktop.ini.
    
    Requirements:
    - Folder must have Read-Only attribute
    - desktop.ini must have Hidden + System attributes
    """
    try:
        import ctypes
        
        # Create desktop.ini content
        ini_path = folder_path / "desktop.ini"
        ini_content = f"[.ShellClassInfo]\nIconResource={icon_path},0\n"
        
        # Write desktop.ini
        ini_path.write_text(ini_content, encoding="utf-8")
        
        # Set file attributes (Hidden + System for ini)
        # FILE_ATTRIBUTE_HIDDEN = 0x02
        # FILE_ATTRIBUTE_SYSTEM = 0x04
        ctypes.windll.kernel32.SetFileAttributesW(str(ini_path), 0x02 | 0x04)
        
        # Set folder attribute (Read Only triggers icon read)
        # FILE_ATTRIBUTE_READONLY = 0x01
        ctypes.windll.kernel32.SetFileAttributesW(str(folder_path), 0x01)
        
        return True
    except Exception as e:
        console.print(f"[dim]Windows icon error: {e}[/dim]")
        return False


def set_icon_macos(folder_path: Path, icon_path: Path) -> bool:
    """
    Set custom icon for a folder on macOS.
    
    Uses fileicon CLI if available, falls back to PyObjC.
    """
    try:
        # Try fileicon CLI first (simpler)
        result = subprocess.run(
            ["fileicon", "set", str(folder_path), str(icon_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    # Fallback to PyObjC
    try:
        from AppKit import NSImage, NSWorkspace
        
        image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
        NSWorkspace.sharedWorkspace().setIcon_forFile_options_(image, str(folder_path), 0)
        return True
    except ImportError:
        console.print("[dim]Install pyobjc for macOS icon support[/dim]")
        return False
    except Exception as e:
        console.print(f"[dim]macOS icon error: {e}[/dim]")
        return False


def set_icon_linux(folder_path: Path, icon_path: Path) -> bool:
    """
    Set custom icon for a folder on Linux (GNOME/Nautilus).
    
    Uses gio command for setting metadata.
    """
    try:
        result = subprocess.run(
            ["gio", "set", "-t", "string", str(folder_path), 
             "metadata::custom-icon", f"file://{icon_path}"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        console.print("[dim]gio command not found (GNOME required)[/dim]")
        return False
    except Exception as e:
        console.print(f"[dim]Linux icon error: {e}[/dim]")
        return False


def set_folder_icon(folder_path: Path, icon_path: Path) -> bool:
    """Set folder icon using the appropriate OS-specific method."""
    system = platform.system()
    
    if system == "Windows":
        return set_icon_windows(folder_path, icon_path)
    elif system == "Darwin":
        return set_icon_macos(folder_path, icon_path)
    else:  # Linux
        return set_icon_linux(folder_path, icon_path)


def hydrate_icons(root: Path) -> Dict[str, bool]:
    """
    Apply icons to all Johnny.Decimal area folders.
    
    Returns:
        Dict mapping folder name to success status
    """
    icon_dir = get_icon_dir(root)
    results = {}
    
    if not icon_dir.exists():
        console.print(f"[dim]Icon directory not found: {icon_dir}[/dim]")
        console.print("[dim]Place icon files (00.ico, 10.ico, etc.) there first.[/dim]")
        return results
    
    for area_name, area_info in AREA_ICONS.items():
        folder_path = root / area_name
        icon_file = icon_dir / area_info["icon"]
        
        if not folder_path.exists():
            results[area_name] = False
            continue
        
        if not icon_file.exists():
            console.print(f"[dim]Icon not found: {icon_file}[/dim]")
            results[area_name] = False
            continue
        
        success = set_folder_icon(folder_path, icon_file)
        results[area_name] = success
        
        if success:
            console.print(f"[green]✓[/green] {area_name} [{area_info['color']}]")
        else:
            console.print(f"[yellow]⚠[/yellow] {area_name} (skipped)")
    
    return results
