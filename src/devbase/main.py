"""
DevBase CLI Main Entry Point (Typer-based)
============================================
Modern CLI using Typer framework for type-safe, declarative commands.
Replaces the legacy argparse-based devbase.py.

Author: DevBase Team
Version: Dynamic (see __init__.py)
"""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from devbase.commands import core, development, navigation, operations, quick, pkm, study, analytics, ai
from devbase.utils.workspace import detect_workspace_root

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

# Register command groups with Progressive Disclosure panels
# Panel names create visual grouping in --help output

# 🟢 ESSENTIALS - Start here (Week 1)
app.add_typer(
    core.app,
    name="core",
    help="🏠 Workspace health & setup",
    rich_help_panel="🟢 Essentials (Start Here)",
)
app.add_typer(
    development.app,
    name="dev",
    help="📦 Create and manage projects",
    rich_help_panel="🟢 Essentials (Start Here)",
)
app.add_typer(
    navigation.app,
    name="nav",
    help="🧭 Navigate folders quickly",
    rich_help_panel="🟢 Essentials (Start Here)",
)

# 🟡 DAILY WORKFLOW - After mastering essentials (Week 2-3)
app.add_typer(
    operations.app,
    name="ops",
    help="📊 Track activities & backup",
    rich_help_panel="🟡 Daily Workflow",
)
app.add_typer(
    quick.app,
    name="quick",
    help="⚡ One-command shortcuts",
    rich_help_panel="🟡 Daily Workflow",
)

# 🔵 ADVANCED - For power users (Week 4+)
app.add_typer(
    pkm.app,
    name="pkm",
    help="🧠 Knowledge graph & linking",
    rich_help_panel="🔵 Advanced",
)
app.add_typer(
    study.app,
    name="study",
    help="📚 Learning & spaced repetition",
    rich_help_panel="🔵 Advanced",
)
app.add_typer(
    analytics.app,
    name="analytics",
    help="📈 Productivity insights",
    rich_help_panel="🔵 Advanced",
)
app.add_typer(
    ai.app,
    name="ai",
    help="🧠 AI-powered features",
    rich_help_panel="🔵 Advanced",
)


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

    if verbose:
        console.print(f"[dim]Workspace: {workspace_root}[/dim]")


# Entry point for console script
def cli_main():
    """Entry point for the installed CLI."""
    app()


if __name__ == "__main__":
    cli_main()
