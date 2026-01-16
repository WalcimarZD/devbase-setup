"""
Quick Action Commands: quickstart, sync, note
==============================================
Composite commands for common workflows and instant knowledge capture.
"""
import re
import subprocess
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from typing_extensions import Annotated

app = typer.Typer(help="Quick action commands")
console = Console()


@app.command()
def note(
    ctx: typer.Context,
    content: Annotated[str, typer.Argument(help="Note content or TIL")],
    edit: Annotated[bool, typer.Option("--edit", "-e", help="Open in VS Code after creating")] = False,
    til: Annotated[bool, typer.Option("--til/--no-til", "-t", help="Save as TIL (default: True)")] = True,
) -> None:
    """
    📝 Instant note capture to knowledge base.
    
    Creates a note with minimal friction (7-line template vs 27-line full template).
    Perfect for quick TILs, ideas, or snippets during flow state.
    
    Examples:
        devbase quick note "Python f-strings support = for debug"
        devbase quick note "OAuth2 PKCE flow prevents token interception" --edit
        devbase quick note "Meeting notes with team" --no-til
    """
    root: Path = ctx.obj["root"]
    
    # Generate slug from content
    slug = re.sub(r'[^\w\s-]', '', content.lower())[:50]
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    # Determine save location
    date = datetime.now()
    if til:
        base_dir = root / "10-19_KNOWLEDGE" / "11_public_garden" / "til"
        # Temporal organization (Fase 4 prep)
        year_dir = base_dir / str(date.year)
        month_dir = year_dir / f"{date.month:02d}-{date.strftime('%B').lower()}"
        save_dir = month_dir
    else:
        save_dir = root / "10-19_KNOWLEDGE" / "11_public_garden" / "notes"
    
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    filepath = save_dir / filename
    
    # Minimal template (7 lines vs 27)
    note_content = f"""---
title: "{content}"
date: {date.strftime('%Y-%m-%d')}
tags: [{"til" if til else "note"}, quick]
---

{content}
"""
    
    # Save
    filepath.write_text(note_content, encoding="utf-8")
    
    console.print()
    console.print(f"[green]✓[/green] Note saved: [cyan]{filepath.relative_to(root)}[/cyan]")
    
    if edit:
        try:
            import shutil
            if shutil.which("code"):
                subprocess.run(["code", "--", str(filepath)], check=False)
                console.print("[dim]Opened in VS Code[/dim]")
        except Exception:
            pass
    
    console.print()


@app.command()
def quickstart(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Project name")],
    template: Annotated[str, typer.Option("--template", "-t", help="Template name")] = "clean-arch",
) -> None:
    """
    🚀 GOLDEN PATH: Zero-touch project bootstrapping.
    
    Creates production-ready project in <60 seconds:
    1. Generate from template
    2. Initialize Git repository
    3. Install dependencies (uv)
    4. Setup pre-commit hooks
    5. Create initial commit
    6. Open in VS Code
    
    Example:
        devbase quick quickstart my-awesome-api
        devbase quick quickstart my-lib --template python-lib
    """
    root: Path = ctx.obj["root"]

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]🚀 Golden Path Bootstrapping[/bold cyan]\n\n"
        f"Project: [yellow]{name}[/yellow]\n"
        f"Template: [dim]{template}[/dim]",
        border_style="cyan"
    ))

    # Use shared logic
    from devbase.utils.templates import generate_project_from_template
    from devbase.services.project_setup import get_project_setup
    
    setup_service = get_project_setup(root)

    # Step 1: Create project
    console.print("\n[bold cyan]Step 1/2:[/bold cyan] Generating project...")
    
    try:
        project_path = generate_project_from_template(
            template_name=template,
            project_name=name,
            root=root,
            interactive=False  # Golden Path = zero prompts
        )
        console.print("[green]✓[/green] Project created\n")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        raise typer.Exit(1)

    # Step 2: Run Golden Path Setup (encapsulated)
    console.print("[bold cyan]Step 2/2:[/bold cyan] Running setup...")
    setup_service.run_golden_path(project_path, name)

    # Success summary
    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Golden Path Complete![/bold green]\n\n"
        f"Project: [cyan]{project_path}[/cyan]\n\n"
        f"[dim]Ready for development![/dim]",
        border_style="green"
    ))


@app.command()
def sync(ctx: typer.Context) -> None:
    """
    🔄 Sync workspace (doctor + hydrate + backup).
    
    This is a maintenance command that runs:
    1. devbase core doctor    (verify workspace health)
    2. devbase core hydrate   (update templates)
    3. devbase ops backup     (create backup)
    
    Useful for weekly workspace maintenance.
    
    Example:
        devbase quick sync
    """
    root: Path = ctx.obj["root"]

    console.print()
    console.print("[bold cyan]🔄 Workspace Sync[/bold cyan]\n")

    # Import command modules
    from rich.panel import Panel

    from devbase.commands.core import doctor, hydrate
    from devbase.commands.operations import backup

    # Step 1: Doctor
    console.print(Panel("[bold]Step 1/3:[/bold] Health Check", border_style="cyan"))
    try:
        doctor(ctx)
    except Exception as e:
        console.print(f"[red]✗ Health check failed: {e}[/red]")

    console.print()

    # Step 2: Hydrate
    console.print(Panel("[bold]Step 2/3:[/bold] Template Sync", border_style="cyan"))
    try:
        ctx_dict = {"root": root, "console": console, "verbose": False}
        mock_ctx = type('obj', (object,), {'obj': ctx_dict})()
        hydrate(mock_ctx, False)
    except Exception as e:
        console.print(f"[yellow]⚠ Template sync issue: {e}[/yellow]")

    console.print()

    # Step 3: Backup
    console.print(Panel("[bold]Step 3/3:[/bold] Backup", border_style="cyan"))
    try:
        backup(ctx)
    except Exception as e:
        console.print(f"[yellow]⚠ Backup issue: {e}[/yellow]")

    console.print()
    console.print("[bold green]✅ Sync complete![/bold green]")
