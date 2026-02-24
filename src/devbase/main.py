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
import os
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from devbase.utils.workspace import detect_workspace_root

logger = logging.getLogger(__name__)

try:
    __version__ = "5.1.0-alpha.4"
except Exception:
    __version__ = "5.1.0-alpha.4"

# Progressive Disclosure panel assignments with logical ordering
# Order is determined by first appearance of each panel during command registration
PANEL_MAP: dict[str, tuple[str, str]] = {
    # name: (help text, panel)
    "core":        ("🏠 [bold green]Workspace Management[/bold green]\nSetup, health checks, and environment repair.", "🟢 Essentials (Start Here)"),
    "dev":         ("📦 [bold green]Project Lifecycle[/bold green]\nScaffold new projects and manage development worktrees.", "🟢 Essentials (Start Here)"),
    "nav":         ("🧭 [bold green]Smart Navigation[/bold green]\nJump between Johnny.Decimal folders instantly.", "🟢 Essentials (Start Here)"),

    "ops":         ("📊 [bold blue]Daily Operations[/bold blue]\nActivity tracking, backups, and automation maintenance.", "🟡 Daily Workflow"),
    "quick":       ("⚡ [bold blue]Productivity Shortcuts[/bold blue]\nOne-command workflows for repetitive tasks.", "🟡 Daily Workflow"),
    "audit":       ("🛡️ [bold blue]System Auditing[/bold blue]\nEnforce naming conventions and Johnny.Decimal integrity.", "🟡 Daily Workflow"),
    "docs":        ("📚 [bold blue]Documentation[/bold blue]\nGenerate and manage workspace documentation.", "🟡 Daily Workflow"),

    "self-update": ("🔄 [bold white]System Update[/bold white]\nUpdate DevBase to the latest version.", "⚙️ System & Maintenance"),

    "ai":          ("🧠 [bold magenta]Cognitive Engine[/bold magenta]\nAI-powered organization, RAG search, and triage.", "🔵 Advanced & AI"),
    "pkm":         ("🧠 [bold magenta]Knowledge Management[/bold magenta]\nBuild and query your personal knowledge graph.", "🔵 Advanced & AI"),
    "analytics":   ("📈 [bold magenta]Usage Analytics[/bold magenta]\nProductivity insights and data-driven reporting.", "🔵 Advanced & AI"),
    "study":       ("📚 [bold magenta]Learning System[/bold magenta]\nSpaced repetition and technical study management.", "🔵 Advanced & AI"),
}

# Initialize Typer app with rich help
app = typer.Typer(
    name="devbase",
    help="""
🚀 [bold cyan]DevBase Elite EOS v5.1.0-alpha.4[/bold cyan]

The elite engineering operating system. Enforces [bold]Johnny.Decimal[/bold] 
organization, automates environments, and provides [bold]AI-driven workflows[/bold].
    """,
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

    Commands are registered in panel order to ensure correct display order.
    """
    eps = entry_points()

    # Python 3.12+ returns a SelectableGroups; 3.10–3.11 returns dict
    if hasattr(eps, "select"):
        command_eps = eps.select(group="devbase.commands")
    else:
        command_eps = eps.get("devbase.commands", [])

    # Convert to list and create a mapping for ordered registration
    eps_list = list(command_eps)
    eps_by_name = {ep.name: ep for ep in eps_list}

    # Define registration order by panel priority
    # Essentials FIRST, then Daily, then Advanced, then any remaining
    # (System & Maintenance via self-update is registered AFTER this function)
    registration_order = [
        # Z. Essentials (Start Here)
        "core", "dev", "nav",
        # Y. Daily Workflow
        "ops", "quick", "audit", "docs",
        # W. Advanced & AI
        "ai", "analytics", "pkm", "study",
        # X. System & Maintenance (registered separately after)
    ]

    # Register in specified order: Essentials → Daily → Advanced (System & Maintenance via @app.command() last)
    registered = set()
    for cmd_name in registration_order:
        if cmd_name in eps_by_name:
            ep = eps_by_name[cmd_name]
            registered.add(cmd_name)
            try:
                cmd_app = ep.load()
                help_text, panel = PANEL_MAP.get(
                    ep.name, (f"{ep.name} commands", "🔵 Advanced & AI")
                )
                app.add_typer(
                    cmd_app,
                    name=ep.name,
                    help=help_text,
                    rich_help_panel=panel,
                )
            except Exception as e:
                print(
                    f"[devbase] WARNING: failed to load plugin '{ep.name}': "
                    f"{type(e).__name__}: {e}",
                    file=sys.stderr,
                )
                logger.debug("Plugin load traceback:", exc_info=True)

    # Register any remaining commands not in the order list
    for ep in eps_list:
        if ep.name not in registered:
            try:
                cmd_app = ep.load()
                help_text, panel = PANEL_MAP.get(
                    ep.name, (f"{ep.name} commands", "🔵 Advanced & AI")
                )
                app.add_typer(
                    cmd_app,
                    name=ep.name,
                    help=help_text,
                    rich_help_panel=panel,
                )
            except Exception as e:
                print(
                    f"[devbase] WARNING: failed to load plugin '{ep.name}': "
                    f"{type(e).__name__}: {e}",
                    file=sys.stderr,
                )
                logger.debug("Plugin load traceback:", exc_info=True)


# Discover and register commands at import-time (Essentials, Daily, Advanced)
_discover_commands()


# ── Self-update command (registered AFTER other commands for correct panel ordering) ─

@app.command(name="self-update", rich_help_panel="⚙️ System & Maintenance")
def self_update() -> None:
    """🔄 Update DevBase to the latest version (works from anywhere)."""
    import subprocess as sp
    import re
    from pathlib import Path

    console.print("[bold]Checking for updates...[/bold]")

    custom_env = os.environ.copy()
    custom_env["UV_PYTHON_PREFERENCE"] = "only-managed"

    # 1. Discover where I was installed from
    try:
        list_result = sp.run(["uv", "tool", "list"], capture_output=True, text=True, env=custom_env)
        # Search for: devbase vX.Y.Z (from file:///D:/path/to/devbase)
        match = re.search(r"devbase .* \(from (file:///|)(.*)\)", list_result.stdout)

        source_path = None
        if match:
            source_path = match.group(2).strip()
            # Clean up Windows URI format if present (e.g., /D:/path -> D:/path)
            if source_path.startswith("/") and source_path[2] == ":":
                source_path = source_path[1:]

            console.print(f"[dim]Installation source detected: {source_path}[/dim]")

        # 2. Try Standard Upgrade first
        result = sp.run(["uv", "tool", "upgrade", "devbase"], capture_output=True, text=True, env=custom_env)

        if result.returncode == 0:
            console.print("[green]✓[/green] DevBase updated via standard upgrade.")
            return

        # 3. Fallback to Source-based Reinstall
        if source_path and Path(source_path).exists():
            console.print(f"[dim]Standard upgrade failed. Re-installing from source...[/dim]")
            # Important: run from the source_path context to be safe
            result = sp.run(
                ["uv", "tool", "install", ".", "--force", "--reinstall", "--with", ".[all]"],
                cwd=source_path,
                capture_output=True,
                text=True,
                env=custom_env
            )

            if result.returncode == 0:
                console.print("[green]✓[/green] DevBase updated successfully from source.")
            else:
                console.print(f"[red]✗[/red] Update failed: {result.stderr.strip()}")
        else:
            console.print(f"[red]✗[/red] Standard upgrade failed and source path not found.")
            console.print("[dim]Try manually: uv tool install <path_to_repo> --force[/dim]")

    except Exception as e:
        console.print(f"[red]✗[/red] Update process error: {e}")


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
    _is_doctor = ctx.invoked_subcommand == "core" and "doctor" in sys.argv
    if ctx.resilient_parsing or _help_requested or _is_setup or _is_doctor:
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


# Entry point for console script
def cli_main():
    """Entry point for the installed CLI."""
    app()


if __name__ == "__main__":
    cli_main()
