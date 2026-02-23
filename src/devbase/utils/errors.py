"""
Error Display Utilities
========================
Structured, rich-formatted error messages with recovery hints.

Standardizes error presentation across all CLI commands.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

console = Console(stderr=True)


def show_error(
    title: str,
    detail: str,
    *,
    hint: str | None = None,
    docs_url: str | None = None,
) -> None:
    """Display a structured error panel with optional recovery guidance.

    Args:
        title: Short error title (e.g., "API Key Missing")
        detail: Explanation of what went wrong
        hint: Actionable fix instruction (Rich markup supported)
        docs_url: Link to relevant documentation
    """
    content = f"[bold red]{title}[/bold red]\n\n{detail}"
    if hint:
        content += f"\n\n[bold]💡 Fix:[/bold] {hint}"
    if docs_url:
        content += f"\n[dim]📘 Docs: {docs_url}[/dim]"
    console.print(Panel(content, border_style="red"))


def show_missing_extra(
    feature_name: str,
    extra_name: str,
    package_name: str = "devbase",
) -> None:
    """Display a clear install hint when an optional extra is missing.

    Args:
        feature_name: Human-readable feature name (e.g., "AI features")
        extra_name: pip extra name (e.g., "ai")
        package_name: Package name (default "devbase")
    """
    show_error(
        f"{feature_name} — Extra Required",
        f"This feature requires the [cyan]{extra_name}[/cyan] optional dependencies.",
        hint=f"Install with: [bold cyan]uv pip install {package_name}[{extra_name}][/bold cyan]",
    )


def require_extra(module_path: str, extra_name: str, feature_name: str) -> bool:
    """Try importing a module and show install hint on ImportError.

    Args:
        module_path: Dotted import path (e.g., "groq")
        extra_name: pip extra name (e.g., "ai")
        feature_name: Human-readable feature name

    Returns:
        True if import succeeds, False otherwise
    """
    import importlib

    try:
        importlib.import_module(module_path)
        return True
    except ImportError:
        show_missing_extra(feature_name, extra_name)
        return False
