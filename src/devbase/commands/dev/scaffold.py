"""
Scaffold Commands
==================
AI-powered project scaffolding and ADR generation.
"""
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.tree import Tree
from typing_extensions import Annotated

app = typer.Typer()
console = Console()
logger = logging.getLogger(__name__)


@app.command(name="blueprint")
def blueprint(
    ctx: typer.Context,
    description: Annotated[str, typer.Argument(help="Descrição do projeto (ex: 'API FastAPI com Redis')")],
) -> None:
    """
    🏗️ Generate Dynamic Project Blueprint (IA).

    Usa IA para gerar uma estrutura de projeto baseada na descrição,
    inspirada em Clean Architecture.
    """
    from devbase.services.blueprint_service import BlueprintService
    from devbase.services.project_setup import get_project_setup

    root: Path = ctx.obj["root"]

    console.print()
    console.print(Panel.fit(
        f"[bold blue]DevBase Blueprint Generator[/bold blue]\n\n"
        f"Request: [cyan]{description}[/cyan]",
        border_style="blue"
    ))

    service = BlueprintService(root)

    with console.status("[bold green]🤖 Generating Blueprint...[/bold green]"):
        try:
            bp = service.generate(description)
        except (ValueError, Exception) as e:
            console.print(f"[red]Failed to generate blueprint: {e}[/red]")
            raise typer.Exit(1)

    target_dir = root / "20-29_CODE" / "21_monorepo_apps" / bp.project_name

    if target_dir.exists():
        console.print(f"[red]Error: Project '{bp.project_name}' already exists at {target_dir}[/red]")
        raise typer.Exit(1)

    # Preview using Rich Tree
    tree = Tree(f"📂 [bold cyan]{bp.project_name}[/bold cyan]")
    for f in bp.files:
        tree.add(f"[green]📄 {f.path}[/green]")

    console.print(tree)
    console.print()

    if Confirm.ask("[bold]Confirmar criação desta estrutura?[/bold]", default=True):
        console.print(f"\n[dim]Writing to {target_dir}...[/dim]")

        written = service.write_to_disk(bp, target_dir)
        for path in written:
            console.print(f"  [green]✓[/green] {path.relative_to(target_dir)}")

        console.print(f"\n[bold green]✅ Project '{bp.project_name}' created successfully![/bold green]")

        if Confirm.ask("Run Golden Path setup? (Git init, venv)", default=True):
            setup_service = get_project_setup(root)
            setup_service.run_golden_path(target_dir, bp.project_name)
    else:
        console.print("[yellow]Aborted.[/yellow]")


@app.command(name="adr-gen")
def adr_gen(
    ctx: typer.Context,
    context: Annotated[str, typer.Option("--context", "-c", help="Context or reasoning for the decision")] = "",
) -> None:
    """
    👻 Ghostwrite an ADR from recent activity.

    Analyses recent 'track' events or uses provided context to generate
    an Architecture Decision Record (MADR format).
    """
    from devbase.services.adr_generator import get_ghostwriter

    root: Path = ctx.obj["root"]
    ghostwriter = get_ghostwriter(root)

    console.print()
    console.print("[bold]ADR Ghostwriter[/bold]")

    final_context = context

    if not final_context:
        console.print("[dim]Scanning recent architecture events...[/dim]")
        events = ghostwriter.find_recent_decisions()
        if events:
            console.print(f"[green]Found {len(events)} relevant events.[/green]")
            lines = [f"- {e['message']} ({e['timestamp']})" for e in events]
            final_context = "\n".join(lines)
        else:
            if not context:
                console.print("[yellow]No recent architecture events found.[/yellow]")
                from rich.prompt import Prompt
                final_context = Prompt.ask("Please provide context for the ADR")

    if final_context:
        path = ghostwriter.generate_draft(final_context)
        if path:
            console.print(Panel.fit(
                f"[bold green]✅ ADR Drafted![/bold green]\n\n"
                f"Location: [cyan]{path}[/cyan]\n"
                f"Review and edit before committing.",
                border_style="green"
            ))
        else:
            console.print("[red]Failed to generate ADR.[/red]")
