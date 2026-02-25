"""
Quick Action Commands: quickstart, sync, note, and Interactive Dashboard
========================================================================
Composite commands for common workflows and interactive center for PKM.
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from typing_extensions import Annotated

app = typer.Typer(help="⚡ Productivity Shortcuts: One-command workflows and Interactive Dashboard.")
console = Console()

def get_pulse_data(root: Path):
    """Extract productivity metrics from workspace Markdown files."""
    data = {
        "oven_tasks": 0,
        "journal_last": "N/A",
        "icebox_items": 0
    }
    
    # 1. OVEN.md tasks
    oven_path = root / "00-09_SYSTEM" / "02_planning" / "OVEN.md"
    try:
        if oven_path.exists():
            content = oven_path.read_text(encoding="utf-8")
            data["oven_tasks"] = len(re.findall(r"-\s*\[\s*\]", content))
    except Exception:
        pass
        
    # 2. JOURNAL.md last entry
    journal_dir = root / "10-19_KNOWLEDGE" / "12_private-vault" / "journal"
    try:
        if journal_dir.exists():
            journals = list(journal_dir.glob("weekly-*.md"))
            if journals:
                latest_journal = max(journals, key=lambda p: p.stat().st_mtime)
                mtime = datetime.fromtimestamp(latest_journal.stat().st_mtime)
                data["journal_last"] = mtime.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
        
    # 3. ICEBOX.md items
    icebox_path = root / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    try:
        if icebox_path.exists():
            content = icebox_path.read_text(encoding="utf-8")
            # Count entries (usually ### [INBOX] or similar)
            data["icebox_items"] = len(re.findall(r"###\s*\[", content))
    except Exception:
        pass
        
    return data

def render_pulse(data):
    """Render the Workspace Pulse panel."""
    oven_label = "tarefa pendente" if data['oven_tasks'] == 1 else "tarefas pendentes"
    icebox_label = "item capturado" if data['icebox_items'] == 1 else "itens capturados"
    
    pulse_content = (
        f"🔥 [bold red]OVEN:[/bold red] {data['oven_tasks']} {oven_label}\n"
        f"📔 [bold blue]JOURNAL:[/bold blue] Última atividade em {data['journal_last']}\n"
        f"🧊 [bold cyan]ICEBOX:[/bold cyan] {data['icebox_items']} {icebox_label}"
    )
    console.print(Panel(pulse_content, title="[bold white]W O R K S P A C E   P U L S E[/bold white]", border_style="bright_blue", expand=False))

def open_in_code(path: Path):
    """Open a path in VS Code ensuring Windows compatibility."""
    try:
        # Use shell=True for Windows and ensure string path
        # Using f-string to ensure quotes around path
        subprocess.run(f'code "{path}"', shell=sys.platform == "win32", check=False)
        console.print(f"[dim]✓ Abrindo {path.name} no VS Code...[/dim]")
    except Exception as e:
        console.print(f"[red]✗ Erro ao abrir VS Code: {e}[/red]")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Interactive Productivity Dashboard entry point."""
    if ctx.invoked_subcommand is not None:
        return

    # Use ServiceContainer to get the root path safely
    services = ctx.obj.get("services")
    if not services:
        from devbase.services.container import ServiceContainer
        services = ServiceContainer(ctx.obj["root"])
    
    root = services.root
    
    # Clear terminal
    if sys.platform == "win32":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run("clear", shell=True)

    console.print()
    # Step 1: Pulse
    pulse_data = get_pulse_data(root)
    render_pulse(pulse_data)
    console.print()

    # Step 2: Interactive Menu
    choice = questionary.select(
        "Selecione uma ação de produtividade:",
        choices=[
            "📖 Ver Forno (OVEN.md)",
            "📝 Escrever no Diário",
            "🔍 Pesquisar no Cookbook",
            "❄️ Capturar para o Icebox",
            "⚙️ Sync Workspace",
            "🚪 Sair"
        ],
        style=questionary.Style([
            ('qmark', 'fg:#673ab7 bold'),
            ('question', 'bold'),
            ('answer', 'fg:#f44336 bold'),
            ('pointer', 'fg:#673ab7 bold'),
            ('highlighted', 'fg:#673ab7 bold'),
            ('selected', 'fg:#cc2127'),
            ('separator', 'fg:#cc2127'),
            ('instruction', ''),
        ])
    ).ask()

    if choice == "📖 Ver Forno (OVEN.md)":
        oven_path = root / "00-09_SYSTEM" / "02_planning" / "OVEN.md"
        if oven_path.exists():
            content = oven_path.read_text(encoding="utf-8")
            tasks = re.findall(r"-\s*\[\s*\]\s*(.*)", content)
            
            if tasks:
                table = Table(title="🔥 Tarefas no Forno", box=None)
                table.add_column("ID", style="dim")
                table.add_column("Tarefa")
                for i, task in enumerate(tasks, 1):
                    table.add_row(str(i), task)
                console.print(table)
            else:
                console.print("[yellow]Nenhuma tarefa pendente no OVEN.md[/yellow]")
            
            if questionary.confirm("Abrir arquivo no VS Code?").ask():
                open_in_code(oven_path)
        else:
            console.print(f"[red]OVEN.md não encontrado em {oven_path}[/red]")

    elif choice == "📝 Escrever no Diário":
        from devbase.commands.pkm import journal
        journal(ctx)

    elif choice == "🔍 Pesquisar no Cookbook":
        query = questionary.text("O que você deseja buscar no Cookbook?").ask()
        if query:
            cookbook_path = root / "10-19_KNOWLEDGE" / "10_references" / "cookbook.md"
            if cookbook_path.exists():
                # Use Select-String logic via Python
                content = cookbook_path.read_text(encoding="utf-8")
                matches = []
                for i, line in enumerate(content.splitlines(), 1):
                    if query.lower() in line.lower():
                        matches.append((i, line.strip()))
                
                if matches:
                    console.print(f"\n[bold green]✓ Encontrado {len(matches)} resultado(s):[/bold green]")
                    for line_no, text in matches:
                        console.print(f"  [dim]L{line_no}:[/dim] {text.replace(query, f'[bold yellow]{query}[/bold yellow]')}")
                else:
                    console.print(f"[yellow]Nenhum resultado para '{query}' no Cookbook.[/yellow]")
            else:
                console.print("[red]Cookbook não encontrado.[/red]")

    elif choice == "❄️ Capturar para o Icebox":
        idea = questionary.text("Qual ideia você deseja capturar?").ask()
        if idea:
            from devbase.commands.pkm import icebox
            icebox(ctx, idea)

    elif choice == "⚙️ Sync Workspace":
        sync(ctx)

    elif choice == "🚪 Sair":
        console.print("[dim]Até logo![/dim]")

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
        open_in_code(filepath)
    
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
