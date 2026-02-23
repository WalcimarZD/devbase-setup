"""
DevBase CLI Main Entry Point (Typer-based)
============================================
Modern CLI using Typer framework with plugin-based command discovery.

Commands are registered via entry_points (pyproject.toml) and loaded
lazily — only the invoked command's module is imported at runtime.

Author: DevBase Team
Version: Dynamic (see __init__.py)
"""
from __future__ import annotations

import logging
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from devbase.utils.workspace import detect_workspace_root

logger = logging.getLogger(__name__)

# Progressive Disclosure panel assignments
# Commands not listed here default to "🔵 Advanced"
PANEL_MAP: dict[str, tuple[str, str]] = {
    # name: (help text, panel)
    "core":      ("🏠 Workspace health & setup",     "🟢 Essentials (Start Here)"),
    "dev":       ("📦 Create and manage projects",    "🟢 Essentials (Start Here)"),
    "nav":       ("🧭 Navigate folders quickly",      "🟢 Essentials (Start Here)"),
    "audit":     ("🛡️ Consistency & Health",          "🟡 Daily Workflow"),
    "ops":       ("📊 Track activities & backup",     "🟡 Daily Workflow"),
    "quick":     ("⚡ One-command shortcuts",          "🟡 Daily Workflow"),
    "docs":      ("📚 Generate documentation",        "🟡 Daily Workflow"),
    "pkm":       ("🧠 Knowledge graph & linking",     "🔵 Advanced"),
    "study":     ("📚 Learning & spaced repetition",  "🔵 Advanced"),
    "analytics": ("📈 Productivity insights",         "🔵 Advanced"),
    "ai":        ("🧠 AI-powered features",           "🔵 Advanced"),
}

# Initialize Typer app with rich help
app = typer.Typer(
    name="devbase",
    help="🚀 DevBase - Personal Engineering Operating System",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Initialize Rich console
console = Console()


def _discover_commands() -> None:
    """Auto-discover and register command plugins via entry_points.

    Each entry point in the 'devbase.commands' group is loaded lazily
    and registered as a Typer sub-app with its panel assignment.
    """
    eps = entry_points()

    # Python 3.12+ returns a SelectableGroups; 3.10–3.11 returns dict
    if hasattr(eps, "select"):
        command_eps = eps.select(group="devbase.commands")
    else:
        command_eps = eps.get("devbase.commands", [])

    for ep in command_eps:
        try:
            cmd_app = ep.load()
            help_text, panel = PANEL_MAP.get(
                ep.name, (f"{ep.name} commands", "🔵 Advanced")
            )
            app.add_typer(
                cmd_app,
                name=ep.name,
                help=help_text,
                rich_help_panel=panel,
            )
        except Exception as e:
            # Always visible — a silent drop here is worse than a noisy warning.
            print(
                f"[devbase] WARNING: failed to load plugin '{ep.name}': "
                f"{type(e).__name__}: {e}",
                file=sys.stderr,
            )
            logger.debug("Plugin load traceback:", exc_info=True)


# Discover and register commands at import-time
_discover_commands()


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        from devbase import __version__
        console.print(f"devbase {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    root: Annotated[
        Optional[Path],
        typer.Option(
            "--root",
            "-r",
            help="Workspace root path (auto-detected if not specified)",
            envvar="DEVBASE_ROOT",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output"),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable colored output"),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show version and exit", callback=version_callback, is_eager=True),
    ] = False,
) -> None:
    """
    DevBase CLI - Global callback for all commands.

    Detects workspace root and stores in context for all subcommands.
    """
    # Disable colors if requested
    if no_color:
        console.no_color = True

    # Skip workspace detection when:
    # - generating shell completions (resilient_parsing)
    # - the user is only asking for help (command body never executes)
    # - running `core setup`, which IS the command that creates the workspace
    _help_requested = "--help" in sys.argv or "-h" in sys.argv
    _is_setup = ctx.invoked_subcommand == "core" and "setup" in sys.argv
    if ctx.resilient_parsing or _help_requested or _is_setup:
        ctx.obj = {"root": root.resolve() if root else Path.cwd(), "console": console, "verbose": verbose}
        return

    # Detect or validate workspace root
    if root:
        workspace_root = root.resolve()
    else:
        workspace_root = detect_workspace_root()

    # Store in context for subcommands
    ctx.obj = {
        "root": workspace_root,
        "console": console,
        "verbose": verbose,
    }

    # Lazy service container — available to all subcommands
    try:
        from devbase.services.container import ServiceContainer
        ctx.obj["services"] = ServiceContainer(workspace_root)
    except Exception:
        pass  # non-fatal; commands that need it will handle absence

    if verbose:
        console.print(f"[dim]Workspace: {workspace_root}[/dim]")


# ── Self-update command ─────────────────────────────────────────────

@app.command(name="self-update")
def self_update() -> None:
    """🔄 Update DevBase to the latest version."""
    import subprocess as sp

    console.print("[bold]Checking for updates...[/bold]")
    result = sp.run(
        ["uv", "pip", "install", "--upgrade", "devbase"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        console.print("[green]✓[/green] DevBase updated successfully.")
    else:
        console.print(f"[red]✗[/red] Update failed: {result.stderr.strip()}")
        console.print("[dim]Try manually: uv pip install --upgrade devbase[/dim]")


# Entry point for console script
def cli_main():
    """Entry point for the installed CLI."""
    app()


if __name__ == "__main__":
    cli_main()
