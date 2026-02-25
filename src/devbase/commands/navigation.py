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


import questionary

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """🧭 Semantic navigation shortcuts."""
    if ctx.invoked_subcommand is None:
        root: Path = ctx.obj["root"]
        locations = get_semantic_locations(root)
        
        # Interactive Selection
        choice = questionary.select(
            "Where do you want to go?",
            choices=[questionary.Choice(title=f"{name} ({locations[name].relative_to(root)})", value=name) 
                     for name in sorted(locations.keys())]
        ).ask()
        
        if choice:
            console.print(str(locations[choice]))

@app.command()
def list(ctx: typer.Context) -> None:
    """📄 List all available semantic locations."""
    root: Path = ctx.obj["root"]
    locations = get_semantic_locations(root)
    
    console.print("\n[bold]Semantic Locations:[/bold]")
    for name in sorted(locations.keys()):
        path = locations[name].relative_to(root)
        console.print(f"  [cyan]{name:12}[/cyan] → [dim]{path}[/dim]")

@app.command()
def goto(
    ctx: typer.Context,
    location: Annotated[str, typer.Argument(help="Semantic location name")] = None,
) -> None:
    """
    🧭 Resolve semantic path for shell navigation.
    
    If location is missing, shows available options.
    """
    root: Path = ctx.obj["root"]
    locations = get_semantic_locations(root)

    if not location or location not in locations:
        if location:
            console.print(f"[red]✗ Unknown location: {location}[/red]")
        
        # Show options and path for shell integration
        for name in sorted(locations.keys()):
            path = locations[name].relative_to(root)
            console.print(f"  [cyan]{name:12}[/cyan] → [dim]{path}[/dim]")
        raise typer.Exit(1)

    # Print path for shell integration
    console.print(str(locations[location]))
