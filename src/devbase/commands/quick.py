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
    til: Annotated[bool, typer.Option("--til", "-t", help="Save as TIL (default)")] = True,
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
                subprocess.run(["code", str(filepath)], check=False)
                console.print("[dim]Opened in VS Code[/dim]")
        except Exception:
            pass
    
    console.print()


@app.command()
def quickstart(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Project name")],
) -> None:
    """
    🚀 Quick project setup (create + init git + open VS Code).
    
    This is a convenience command that combines:
    1. devbase dev new <name>
    2. cd <project>
    3. git init
    4. git add .
    5. git commit -m "Initial commit"
    6. code .  (if VS Code is installed)
    
    Example:
        devbase quick quickstart my-awesome-api
    """
    root: Path = ctx.obj["root"]

    console.print()
    console.print(f"[bold cyan]🚀 QuickStart: {name}[/bold cyan]\n")

    # Step 1: Create project
    console.print("[bold]Step 1/5:[/bold] Creating project...")
    from devbase.utils.templates import generate_project_from_template

    try:
        project_path = generate_project_from_template(
            template_name="clean-arch",
            project_name=name,
            root=root,
            interactive=False  # Use defaults for speed
        )
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]")
        raise typer.Exit(1)

    console.print("[green]✓ Project created[/green]\n")

    # Step 2: Git init
    console.print("[bold]Step 2/5:[/bold] Initializing Git...")
    try:
        subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
        console.print("[green]✓ Git initialized[/green]\n")
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠ Git init failed (continuing...)[/yellow]\n")

    # Step 3: Git add
    console.print("[bold]Step 3/5:[/bold] Adding files...")
    try:
        subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
        console.print("[green]✓ Files staged[/green]\n")
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠ Git add failed (continuing...)[/yellow]\n")

    # Step 4: Git commit
    console.print("[bold]Step 4/5:[/bold] Creating initial commit...")
    try:
        subprocess.run(
            ["git", "commit", "-m", "Initial commit from DevBase"],
            cwd=project_path,
            check=True,
            capture_output=True
        )
        console.print("[green]✓ Initial commit created[/green]\n")
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠ Git commit failed (continuing...)[/yellow]\n")

    # Step 5: Open in VS Code (if available)
    console.print("[bold]Step 5/5:[/bold] Opening in VS Code...")
    try:
        import shutil
        if shutil.which("code"):
            subprocess.run(["code", str(project_path)], check=True)
            console.print("[green]✓ Opened in VS Code[/green]\n")
        else:
            console.print("[dim]VS Code not found (skipping)[/dim]\n")
    except Exception:
        console.print("[dim]Could not open VS Code (skipping)[/dim]\n")

    # Success!
    from rich.panel import Panel
    console.print(Panel.fit(
        f"[bold green]✅ QuickStart Complete![/bold green]\n\n"
        f"Your project is ready at:\n[cyan]{project_path}[/cyan]\n\n"
        f"[dim]Git repository initialized with initial commit.[/dim]",
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
        # Create minimal context for commands
        class MockArgs:
            def __init__(self):
                self.force = False
                self.dry_run = False

        doctor(ctx)
    except Exception as e:
        console.print(f"[red]✗ Health check failed: {e}[/red]")

    console.print()

    # Step 2: Hydrate
    console.print(Panel("[bold]Step 2/3:[/bold] Template Sync", border_style="cyan"))
    try:
        ctx_dict = {"root": root, "console": console, "verbose": False}
        mock_ctx = type('obj', (object,), {'obj': ctx_dict})()

        class HydrateArgs:
            force = False

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
