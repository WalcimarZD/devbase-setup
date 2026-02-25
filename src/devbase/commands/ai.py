"""
AI Commands: organize, insights, config, routine, RAG
=====================================================
AI-powered commands for workspace management and cognitive assistance.

Commands:
    devbase ai config           - Configure AI provider API key
    devbase ai organize <path>  - Suggest file organization
    devbase ai insights         - Generate workspace insights
    devbase ai status           - Check AI configuration status
    devbase ai index            - Index workspace for semantic search
    devbase ai chat <prompt>    - Chat with your workspace (RAG)
    devbase ai classify         - Classify text into categories
    devbase ai summarize        - Summarize long text
    devbase ai routine briefing - Daily morning briefing
    devbase ai routine triage   - Inbox triage and classification
"""
import os
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

import typer
import questionary
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from typing_extensions import Annotated

app = typer.Typer(
    name="ai",
    help="🤖 AI-powered workspace commands",
    no_args_is_help=True,
)

routine_app = typer.Typer(
    name="routine",
    help="📅 Routine management (briefing, triage)",
    no_args_is_help=True,
)
app.add_typer(routine_app, name="routine")

console = Console()


def _get_service(ctx: typer.Context):
    """Get the AIService from the container."""
    from devbase.services.container import ServiceContainer
    root = ctx.obj.get("root", Path.cwd())
    return ServiceContainer(root).ai


def _get_provider(ctx: typer.Context):
    """Get the active provider from the AIService."""
    return _get_service(ctx).provider


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def config(ctx: typer.Context) -> None:
    """Configure AI provider API key.
    
    Interactively prompts for and saves the Groq API key
    to config.toml for persistent use.
    """
    import toml
    from devbase.utils.paths import get_config_path
    
    root: Path = ctx.obj["root"]
    config_file = get_config_path(root)
    
    console.print("\n[bold]🤖 AI Configuration[/bold]\n")
    
    # Prompt for Provider
    provider_name = questionary.select(
        "Select AI Provider",
        choices=["groq", "mock"],
        default="groq"
    ).ask()
    
    # Load existing config if present
    existing_config: dict = {}
    if config_file.exists():
        try:
            existing_config = toml.load(config_file)
        except Exception:
            pass
    
    if "ai" not in existing_config:
        existing_config["ai"] = {}
    
    existing_config["ai"]["provider"] = provider_name
    
    if provider_name == "groq":
        console.print("\nGet your API key at: [cyan]https://console.groq.com/keys[/cyan]\n")
        
        # Check current key status
        current_key = existing_config.get("ai", {}).get("groq_api_key", "")
        if current_key:
            masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "****"
            console.print(f"Current key: [dim]{masked}[/dim]\n")
        
        # Prompt for API key
        api_key = typer.prompt(
            "Enter Groq API Key",
            hide_input=True,
            default="",
        )
        
        if api_key:
            existing_config["ai"]["groq_api_key"] = api_key
    
    # Save config
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            toml.dump(existing_config, f)
        
        console.print(f"\n[green]✓[/green] Configuration written successfully.")
        console.print(f"[dim]Saved to: {config_file}[/dim]")
        
        # Test connection
        console.print("\n[dim]Testing connection...[/dim]")
        try:
            service = _get_service(ctx)
            service.provider.validate_connection()
            console.print(f"[green]✓[/green] Connection successful! Active provider: [bold]{provider_name}[/bold]")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Connection test failed: {e}")
    
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to save configuration: {e}")
        raise typer.Exit(1)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def organize(ctx: typer.Context,
    path: Annotated[
        Optional[str], 
        typer.Argument(help="File or directory to organize")
    ] = None,
    auto: Annotated[
        bool,
        typer.Option("--auto", "-a", help="Move file automatically without confirmation"),
    ] = False,
) -> None:
    """Suggest organization for a file using AI."""
    import questionary
    
    # Interactive selection if path is missing
    if not path:
        console.print("[yellow]ℹ No path provided. Entering interactive mode...[/yellow]")
        path = questionary.text(
            "Which file or directory do you want to organize?",
            instruction="Enter path (e.g., ./my-file.txt or . )"
        ).ask()
        
        if not path:
            console.print("[red]✗[/red] Operation cancelled.")
            return

    file_path = Path(path)

    if not file_path.exists():
        console.print(f"[red]✗[/red] File not found: {path}")
        raise typer.Exit(1)
    
    workspace_root = ctx.obj.get("root") if ctx and ctx.obj else None
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        progress.add_task(description="🤖 Analyzing file...", total=None)
        try:
            service = _get_service(ctx)
            suggestion = service.suggest_organization(str(file_path), workspace_root=workspace_root)
        except Exception as e:
            console.print(f"[red]✗[/red] AI analysis failed: {e}")
            raise typer.Exit(1)
    
    confidence_emoji = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.5 else "🔴"
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Label", style="dim")
    table.add_column("Value")
    table.add_row("Destination:", f"[cyan]{suggestion.destination}[/cyan]")
    if suggestion.new_name:
        table.add_row("New Name:", f"[cyan]{suggestion.new_name}[/cyan]")
    table.add_row("Confidence:", f"{confidence_emoji} {int(suggestion.confidence * 100)}%")
    table.add_row("", "")
    table.add_row("Reasoning:", suggestion.reasoning)
    
    console.print(Panel(table, title="[bold]📁 Organization Suggestion[/bold]", border_style="blue"))
    
    # ── Execution Logic ──────────────────────────────────────────────────
    
    target_dir = (workspace_root / suggestion.destination) if workspace_root else Path(suggestion.destination)
    new_file_name = suggestion.new_name or file_path.name
    final_path = target_dir / new_file_name
    
    def perform_move():
        try:
            # Ensure destination exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Metadata Injection (for Markdown files)
            if file_path.suffix.lower() == ".md" and suggestion.metadata:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    
                    # Today's date
                    from datetime import date
                    today = date.today().isoformat()
                    
                    # Build Frontmatter
                    meta = suggestion.metadata
                    header = "---\n"
                    header += f"title: \"{meta.get('title', 'Untitled')}\"\n"
                    header += f"description: \"{meta.get('description', '')}\"\n"
                    header += f"version: \"{meta.get('version', '1.0.0')}\"\n"
                    header += f"generated: \"{today}\"\n"
                    header += f"scope: \"{meta.get('scope', 'General')}\"\n"
                    header += "---\n\n"
                    
                    # Avoid double header if already exists
                    if not content.startswith("---"):
                        file_path.write_text(header + content, encoding="utf-8")
                except Exception as e:
                    console.print(f"[dim]Note: Metadata injection failed: {e}[/dim]")

            # Check for conflict
            if final_path.exists():
                console.print(f"[yellow]⚠ Conflict:[/yellow] {final_path} already exists.")
                if not questionary.confirm("Overwrite?").ask():
                    console.print("[red]✗[/red] Aborted.")
                    return

            # Perform Move
            shutil.move(str(file_path), str(final_path))
            console.print(f"\n[green]✓ Successfully moved to:[/green] [bold]{final_path}[/bold]")
        except Exception as e:
            console.print(f"[red]✗ Failed to move file: {e}[/red]")

    if auto:
        perform_move()
    else:
        if questionary.confirm(f"\nMove file to {suggestion.destination}?").ask():
            perform_move()
        else:
            console.print("\n[dim]No changes made. Use --auto to skip this prompt.[/dim]")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def insights(ctx: typer.Context,
    path: Annotated[Optional[str], typer.Option("--path", "-p", help="Directory to analyze")] = None,
) -> None:
    """Generate insights about workspace structure."""
    workspace_path = Path(path) if path else (ctx.obj["root"] if ctx and ctx.obj and ctx.obj.get("root") else Path.cwd())
    if not workspace_path.exists():
        console.print(f"[red]✗[/red] Path not found: {workspace_path}")
        raise typer.Exit(1)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        progress.add_task(description="🔍 Analyzing workspace structure...", total=None)
        try:
            service = _get_service(ctx)
            analysis = service.generate_insights(str(workspace_path))
        except Exception as e:
            console.print(f"[red]✗[/red] AI analysis failed: {e}")
            raise typer.Exit(1)
    
    score_emoji = "🟢" if analysis.score >= 80 else "🟡" if analysis.score >= 60 else "🔴"
    console.print(Panel(f"[bold]{score_emoji} Organization Score: {analysis.score}/100[/bold]", title="[bold]📊 Workspace Analysis[/bold]", border_style="blue"))
    
    if not analysis.insights:
        console.print("\n[green]✓[/green] No significant issues found!")
        return

    console.print("\n[bold]### Insights[/bold]\n")
    severity_icons = {"warning": "⚠️", "suggestion": "💡", "info": "ℹ️"}
    for insight in analysis.insights:
        icon = severity_icons.get(insight.severity, "•")
        color = {"architecture": "magenta", "optimization": "cyan", "organization": "green"}.get(insight.category, "white")
        console.print(f"{icon} [bold]{insight.title}[/bold]")
        console.print(f"   [dim][{color}]{insight.category}[/{color}][/dim]")
        console.print(f"   {insight.description}\n")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def status(ctx: typer.Context) -> None:
    """Check AI provider configuration status."""
    console.print("\n[bold]🤖 AI Status[/bold]\n")
    
    try:
        service = _get_service(ctx)
        provider = service.provider
        provider_type = provider.__class__.__name__
        
        console.print(f"Active Provider: [bold cyan]{provider_type}[/bold cyan]")
        
        # Test connection
        console.print("\n[dim]Testing connection...[/dim]")
        provider.validate_connection()
        console.print("[green]✓[/green] Connection: OK")
        
        if hasattr(provider, "model"):
             console.print(f"[green]✓[/green] Model: {provider.model}")
             
    except Exception as e:
        console.print(f"[red]✗[/red] AI Status check failed: {e}")


@app.command("index")
def index(
    ctx: typer.Context,
    rebuild: Annotated[bool, typer.Option("--rebuild", help="Force rebuild of entire index")] = False,
) -> None:
    """🔍 Index workspace for semantic search (Local RAG)."""
    try:
        from devbase.services.search_engine import SearchEngine
    except ImportError as e:
        console.print(f"[red]✗ System modules missing:[/red] {e}")
        raise typer.Exit(1)

    engine = SearchEngine()
    root = ctx.obj["root"]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Indexing Knowledge Graph...", total=None)
        try:
            # We assume rebuild_index takes a progress callback or handles it internally
            engine.rebuild_index(root)
            progress.update(task, description="[green]✓ Knowledge Graph indexed.")
        except Exception as e:
            console.print(f"[red]✗ Indexing failed:[/red] {e}")
            raise typer.Exit(1)
    console.print(Panel("[bold green]✓ Semantic Index Ready[/bold green]\nYou can now use [cyan]devbase ai chat[/cyan] for context-aware questions.", border_style="green"))


@app.command("chat")
def chat(
    ctx: typer.Context,
    prompt: Annotated[List[str], typer.Argument(help="Message to AI")],
    temperature: Annotated[float, typer.Option("--temp", "-t", help="Creativity (0.0-1.0)")] = 0.2,
) -> None:
    """💬 Chat with your workspace using RAG (Context-Aware)."""
    service = _get_service(ctx)
    provider = service.provider
    
    # Re-join prompt if it was split by shell
    final_user_prompt = " ".join(prompt)
    
    # Try RAG Retrieval
    context = ""
    try:
        from devbase.services.search_engine import SearchEngine
        engine = SearchEngine()
        with Progress(SpinnerColumn(), TextColumn("[dim]Consulting Knowledge Base...[/dim]"), console=console, transient=True) as progress:
             progress.add_task("searching", total=None)
             results = engine.search(final_user_prompt, limit=5)
             if results:
                 context = "\n\n".join([f"SOURCE [{r.file_path}]:\n{r.content}" for r in results])
    except Exception:
        pass

    final_prompt = final_user_prompt
    if context:
        final_prompt = f"""You are the DevBase AI Assistant. Answer the question using ONLY the provided workspace context.
If the answer is not in the context, state that you don't know based on the current workspace data.

WORKSPACE CONTEXT:
{context}

USER QUESTION: {final_user_prompt}
"""

    with Progress(SpinnerColumn(), TextColumn("[bold cyan]Synthesizing response...[/bold cyan]"), console=console, transient=True) as progress:
        progress.add_task("thinking", total=None)
        try:
            response_text = provider.complete(final_prompt, temperature=temperature)
            console.print()
            console.print(Panel(response_text, title="[bold green]🤖 Workspace Intelligence[/bold green]", border_style="green", padding=(1, 2)))
        except Exception as e:
            console.print(f"[red]✗ Synthesis error:[/red] {e}")
            raise typer.Exit(1)


@app.command("classify")
def classify(
    ctx: typer.Context,
    text: Annotated[str, typer.Argument(help="Text to classify")],
    categories: Annotated[str, typer.Option("--categories", "-c", help="Target categories")] = "feature,bug,docs,refactor",
) -> None:
    """🏷️ Classify text into a technical category."""
    service = _get_service(ctx)
    category_list = [c.strip() for c in categories.split(",")]
    
    with Progress(SpinnerColumn(), TextColumn("[bold blue]Classifying semantic intent...[/bold blue]"), console=console, transient=True) as progress:
        progress.add_task("task", total=None)
        try:
            result = service.classify(text, category_list)
            console.print(f"\n[bold]Classification:[/bold] [cyan]{result}[/cyan]")
        except Exception as e:
            console.print(f"[red]✗[/red] Classification failed: {e}")


@app.command("summarize")
def summarize(
    ctx: typer.Context,
    text: Annotated[str, typer.Argument(help="Text to summarize")],
    max_length: Annotated[int, typer.Option("--max-length", "-l")] = 100,
) -> None:
    """📝 Generate a technical executive summary."""
    service = _get_service(ctx)
    
    with Progress(SpinnerColumn(), TextColumn("[bold magenta]Synthesizing summary...[/bold magenta]"), console=console, transient=True) as progress:
        progress.add_task("task", total=None)
        try:
            result = service.summarize(text, max_length)
            console.print(Panel(result, title="[bold]📝 Executive Summary[/bold]", border_style="magenta"))
        except Exception as e:
            console.print(f"[red]✗[/red] Summary failed: {e}")


@app.command("draft")
def draft(
    ctx: typer.Context,
    message: Annotated[Optional[str], typer.Argument(help="Commit message to analyze")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """📝 Generate a technical note based on a Git commit."""
    import subprocess
    import json as json_lib
    
    # Get message if not provided
    if not message:
        try:
            message = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%B"], 
                stderr=subprocess.DEVNULL, 
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            if not json_output:
                console.print("[red]✗[/red] Failed to get last commit message. Are you in a Git repo?")
            raise typer.Exit(1)
    
    if not message:
        if not json_output:
            console.print("[yellow]⚠[/yellow] Empty commit message.")
        return

    try:
        service = _get_service(ctx)
        if json_output:
            suggestion = service.suggest_draft(message)
            console.print(json_lib.dumps(suggestion))
            return

        with Progress(SpinnerColumn(), TextColumn("[bold cyan]Drafting technical note...[/bold cyan]"), console=console, transient=True) as progress:
            progress.add_task("thinking", total=None)
            suggestion = service.suggest_draft(message)
            
            note = suggestion.get("note", "No note generated.")
            category = suggestion.get("category", "JOURNAL").upper()
            
            console.print()
            console.print(Panel(
                f"[bold]Note:[/bold] {note}\n[bold]Category:[/bold] [cyan]{category}[/cyan]",
                title="[bold green]📝 AI Draft Suggestion[/bold green]",
                border_style="green"
            ))
            
    except Exception as e:
        if not json_output:
            console.print(f"[red]✗ Drafting failed:[/red] {e}")
        raise typer.Exit(1)


@routine_app.command("briefing")
def briefing(ctx: typer.Context) -> None:
    """🌅 High-level morning briefing (Status & Goals)."""
    try:
        from devbase.services.routine_agent import RoutineAgent
    except ImportError as e:
        console.print(f"[red]✗ System modules missing:[/red] {e}")
        raise typer.Exit(1)

    root = ctx.obj["root"]
    agent = RoutineAgent(root_path=root)
    
    with Progress(SpinnerColumn(), TextColumn("[bold yellow]Generating daily briefing...[/bold yellow]"), console=console, transient=True) as progress:
        progress.add_task("briefing", total=None)
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        summary = agent.generate_daybook_summary(yesterday_str)
        pending = agent.get_yesterday_pending()

    # ── UI Display ───────────────────────────────────────────────────
    
    console.print(Panel.fit(
        f"[bold cyan]Good Morning![/bold cyan]\nToday is {datetime.now().strftime('%A, %B %d')}",
        border_style="blue"
    ))

    # Yesterday's Narrative
    console.print(Panel(
        summary.log_narrative,
        title="[bold]📅 Yesterday Recap[/bold]",
        subtitle=f"Commits: {summary.metrics.get('commits', 0)}",
        border_style="dim"
    ))

    # Pending Tasks
    table = Table(show_header=False, box=None, padding=(0, 1))
    for task in pending:
        table.add_row(f"  [yellow]➜[/yellow] {task}")
    
    console.print(Panel(table, title="[bold yellow]🔜 Pending from Journal[/bold yellow]", border_style="yellow"))


@routine_app.command("triage")
def triage(
    ctx: typer.Context,
    auto: Annotated[bool, typer.Option("--auto", "-a", help="Move files automatically")] = False,
) -> None:
    """📥 Intelligent Inbox Triage."""
    try:
        from devbase.services.routine_agent import RoutineAgent
    except ImportError as e:
        console.print(f"[red]✗ System modules missing:[/red] {e}")
        raise typer.Exit(1)

    root = ctx.obj["root"]
    agent = RoutineAgent(root_path=root)
    files = agent.scan_inbox()
    
    if not files:
        console.print(Panel("[green]✓ Inbox is clean. You are in total control![/green]", title="[bold]📥 Triage[/bold]", border_style="green"))
        return

    console.print(f"\n[bold]Found {len(files)} items in Inbox.[/bold]\n")

    for file_path in files:
        suggestion = None
        # 1. AI Analysis (with Spinner)
        with Progress(SpinnerColumn(), TextColumn(f"[cyan]Analyzing [bold]{file_path.name}[/bold]...[/cyan]"), console=console, transient=True) as progress:
            progress.add_task("analyze", total=None)
            try:
                from devbase.services.container import ServiceContainer
                service = ServiceContainer(root).ai
                suggestion = service.suggest_organization(str(file_path), workspace_root=root)
            except Exception as e:
                console.print(f"   [red]✗ AI Error:[/red] {e}")
                continue

        # 2. Results and Interaction (Outside Progress context)
        if suggestion:
            console.print(f"📄 [bold]{file_path.name}[/bold]")
            console.print(f"   [dim]Target:[/dim] [green]{suggestion.destination}[/green]")
            console.print(f"   [dim]Reason:[/dim] {suggestion.reasoning}\n")
            
            if auto or questionary.confirm(f"   Move to {suggestion.destination}?").ask():
                agent.move_to_category(file_path, suggestion.destination)
                console.print(f"   [green]✓ Organized.[/green]")
            else:
                console.print(f"   [yellow]⚠ Skipped.[/yellow]")
        
        console.print("[dim]──────────────────────────────────────────────────[/dim]")

