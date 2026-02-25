"""
DevBase CLI - Pure Router
===========================
Architecture: Router Pattern (2026)
- ZERO commands registered directly in this file.
- All functionality coupled via sub-apps (Groups).
- Deterministic help ordering via ASCII-first space prefix.
"""
from __future__ import annotations

import logging
import os
import sys
from importlib.metadata import entry_points, version, PackageNotFoundError
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from devbase.utils.workspace import detect_workspace_root

logger = logging.getLogger(__name__)

# Version Marker
try:
    __version__ = "5.1.0-alpha.5"
except Exception:
    __version__ = "5.1.0-alpha.5"

# Unified Panel Mapping (Forced ASCII Ordering)
PANEL_MAP: dict[str, tuple[str, str]] = {
    "core":        ("🏠 [bold green]Workspace Management[/bold green]\nSetup and health checks.", " A. 🟢 Essentials (Start Here)"),
    "dev":         ("📦 [bold green]Project Lifecycle[/bold green]\nScaffold and worktrees.", " A. 🟢 Essentials (Start Here)"),
    "nav":         ("🧭 [bold green]Smart Navigation[/bold green]\nJump folders instantly.", " A. 🟢 Essentials (Start Here)"),
    
    "ops":         ("📊 [bold blue]Daily Operations[/bold blue]\nTracking and backups.", "B. 🟡 Daily Workflow"),
    "quick":       ("⚡ [bold blue]Productivity Shortcuts[/bold blue]\nShortcuts.", "B. 🟡 Daily Workflow"),
    "audit":       ("🛡️ [bold blue]System Auditing[/bold blue]\nIntegrity checks.", "B. 🟡 Daily Workflow"),
    "docs":        ("📚 [bold blue]Documentation[/bold blue]\nDocs management.", "B. 🟡 Daily Workflow"),
    
    "ai":          ("🧠 [bold magenta]Cognitive Engine[/bold magenta]\nAI and RAG search.", "C. 🔵 Advanced & AI"),
    "pkm":         ("🧠 [bold magenta]Knowledge Management[/bold magenta]\nKnowledge graph.", "C. 🔵 Advanced & AI"),
    "analytics":   ("📈 [bold magenta]Usage Analytics[/bold magenta]\nReports.", "C. 🔵 Advanced & AI"),
    "study":       ("📚 [bold magenta]Learning System[/bold magenta]\nSpaced repetition.", "C. 🔵 Advanced & AI"),
    
    "system":      ("⚙️ [bold white]System Maintenance[/bold white]\nUpdate environment.", "D. ⚙️ System & Maintenance"),
}

# App Router Initialization
app = typer.Typer(
    name="devbase",
    help=f"""
🚀 [bold cyan]DevBase Elite EOS v{__version__}[/bold cyan]

The elite engineering operating system. Enforces [bold]Johnny.Decimal[/bold] 
organization and provides [bold]AI-driven workflows[/bold].
    """,
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()

def _register_subapps() -> None:
    """Couples all sub-modules via entry_points. No commands allowed here."""
    eps = entry_points()
    
    # Select our command group
    if hasattr(eps, "select"):
        command_eps = eps.select(group="devbase.commands")
    else:
        command_eps = eps.get("devbase.commands", [])

    for ep in command_eps:
        try:
            sub_app = ep.load()
            # Determine which panel this sub-app belongs to
            help_text, panel = PANEL_MAP.get(
                ep.name, (f"{ep.name} module", "C. 🔵 Advanced & AI")
            )
            # Standardized coupling
            app.add_typer(
                sub_app,
                name=ep.name,
                help=help_text,
                rich_help_panel=panel,
            )
        except Exception as e:
            print(f"[devbase] WARNING: failed to load plugin '{ep.name}': {e}", file=sys.stderr)

# Execute Router Coupling
_register_subapps()

# ── Global Callbacks ────────────────────────────────────────────────

def version_callback(value: bool) -> None:
    if value:
        console.print(f"devbase {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    ctx: typer.Context,
    root: Annotated[Optional[Path], typer.Option("--root", "-r", envvar="DEVBASE_ROOT")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    no_color: Annotated[bool, typer.Option("--no-color")] = False,
    version: Annotated[bool, typer.Option("--version", "-V", callback=version_callback, is_eager=True)] = False,
) -> None:
    if no_color: console.no_color = True
    
    # Context initialization for sub-apps
    _is_sys = ctx.invoked_subcommand in ["core", "system"]
    if ctx.resilient_parsing or "--help" in sys.argv or "-h" in sys.argv or _is_sys:
        ctx.obj = {"root": root.resolve() if root else Path.cwd(), "console": console, "verbose": verbose}
        return

    workspace_root = root.resolve() if root else detect_workspace_root()
    ctx.obj = {"root": workspace_root, "console": console, "verbose": verbose}

    try:
        from devbase.services.container import ServiceContainer
        ctx.obj["services"] = ServiceContainer(workspace_root)
    except Exception: pass

# Entry Point
def cli_main():
    app()

if __name__ == "__main__":
    cli_main()
