"""
DevBase Theme System - Semantic Color Palette
==============================================
Centralized color definitions following cognitive ergonomics principles.

Based on Ergonomic Report recommendations:
- Reduce visual noise ("Christmas Tree" syndrome)
- Use colors semantically (not decoratively)
- Reserve highlights for actionable items
"""
from rich.style import Style
from rich.theme import Theme


# === SEMANTIC COLOR CONSTANTS ===
# Following cognitive load reduction principles

class Colors:
    """Semantic color definitions for consistent CLI output."""
    
    # Status Indicators (Traffic Light Pattern)
    SUCCESS = "green"           # Universal "proceed" signal
    ERROR = "red"               # Universal "stop" signal, requires attention
    WARNING = "yellow"          # Caution, non-blocking
    
    # Information Hierarchy
    PRIMARY = "default"         # Main text, neutral for extended reading
    SECONDARY = "dim"           # Metadata, can be ignored (timestamps, paths)
    EMPHASIS = "bold"           # Important but not colored
    
    # Actionable Elements
    ACTION = "cyan"             # Reserved for user commands/inputs
    LINK = "blue underline"     # Clickable or navigable items
    
    # Structure (non-competing)
    BORDER = "dim"              # Panels, tables, dividers
    HEADER = "bold"             # Section headers (no color)
    
    # Decorative (use sparingly)
    ACCENT = "magenta"          # Rare highlight for special content


class Icons:
    """
    Semantic icons for CLI output.
    
    Rule: Only use icons that communicate status/meaning.
    Avoid decorative icons (🚀, 🎉) in routine messages.
    """
    
    # Status (functional - keep these)
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    
    # Progress
    PENDING = "○"
    COMPLETE = "●"
    IN_PROGRESS = "◐"
    
    # Navigation
    ARROW_RIGHT = "→"
    ARROW_LEFT = "←"
    BULLET = "•"
    
    # Special (use only for emphasis)
    STAR = "★"
    
    # Avoid in routine messages:
    # 🚀 🎉 🎊 📦 🔥 (These become noise when overused)


# === RICH THEME ===
# Pre-configured theme for consistent styling

DEVBASE_THEME = Theme({
    # Status
    "success": Style(color="green"),
    "error": Style(color="red", bold=True),
    "warning": Style(color="yellow"),
    
    # Information
    "primary": Style(),
    "secondary": Style(dim=True),
    "emphasis": Style(bold=True),
    
    # Actions
    "action": Style(color="cyan"),
    "command": Style(color="cyan", bold=True),
    
    # Structure
    "border": Style(dim=True),
    "header": Style(bold=True),
    "title": Style(bold=True),
    
    # Paths and metadata
    "path": Style(dim=True),
    "timestamp": Style(dim=True),
    
    # Special
    "accent": Style(color="magenta"),
})


def styled(text: str, style: str) -> str:
    """
    Helper to wrap text in Rich markup.
    
    Usage:
        console.print(styled("Success!", "success"))
        # Instead of: console.print("[green]Success![/green]")
    """
    return f"[{style}]{text}[/{style}]"


def success(message: str) -> str:
    """Format success message with icon."""
    return f"[success]{Icons.SUCCESS}[/success] {message}"


def error(message: str) -> str:
    """Format error message with icon."""
    return f"[error]{Icons.ERROR}[/error] {message}"


def warning(message: str) -> str:
    """Format warning message with icon."""
    return f"[warning]{Icons.WARNING}[/warning] {message}"


def info(message: str) -> str:
    """Format info message with icon."""
    return f"[secondary]{Icons.INFO}[/secondary] {message}"


def command(cmd: str) -> str:
    """Format a command the user should type."""
    return f"[command]{cmd}[/command]"


def path(filepath: str) -> str:
    """Format a file path (de-emphasized)."""
    return f"[path]{filepath}[/path]"
