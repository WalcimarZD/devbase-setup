"""
Navigation Commands: goto
==========================
Semantic navigation shortcuts for Johnny.Decimal structure.
"""
from pathlib import Path

import typer
from rich.console import Console
from typing_extensions import Annotated

from devbase.utils.workspace import get_semantic_locations

app = typer.Typer(help="Navigation commands")
console = Console()


@app.command()
def goto(
    ctx: typer.Context,
    location: Annotated[str, typer.Argument(help="Semantic location name")],
) -> None:
    """
    🧭 Navigate to semantic workspace locations.
    
    Available locations:
    - code: Main application projects
    - packages: Shared libraries/packages
    - knowledge: Public notes and documentation
    - vault: Private vault (Air-Gap protected)
    - ai: AI models and configuration
    - backups: Backup storage
    - inbox: Temporary file inbox
    - templates: Project templates
    - dotfiles: Configuration dotfiles
    
    Example:
        devbase nav goto code      # → 20-29_CODE/21_monorepo_apps
        devbase nav goto vault     # → 10-19_KNOWLEDGE/12_private_vault
    
    Shell Integration:
        Add to ~/.bashrc or ~/.zshrc:
        
        goto() {
            cd $(devbase nav goto "$1")
        }
        
        Then use: goto code
    """
    root: Path = ctx.obj["root"]

    locations = get_semantic_locations(root)

    if location not in locations:
        console.print(f"[red]✗ Unknown location: {location}[/red]\n")
        console.print("[bold]Available locations:[/bold]")
        for name in sorted(locations.keys()):
            path = locations[name].relative_to(root)
            console.print(f"  [cyan]{name:12}[/cyan] → [dim]{path}[/dim]")
        raise typer.Exit(1)

    target = locations[location]

    # Print path for shell integration
    console.print(str(target))
