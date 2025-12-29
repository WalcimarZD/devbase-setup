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
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
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


def _get_provider():
    """Get the configured LLM provider (Groq)."""
    try:
        from devbase.ai.providers.groq import GroqProvider
        return GroqProvider()
    except ImportError:
        console.print(
            "[red]✗[/red] AI features require the 'groq' package.\n"
            "Install with: [cyan]pip install devbase[ai][/cyan]"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize AI provider: {e}")
        raise typer.Exit(1)


def _get_service():
    """Get the AIService with configured provider."""
    from devbase.ai.service import AIService
    provider = _get_provider()
    return AIService(provider)


@app.command()
def config() -> None:
    """Configure AI provider API key.
    
    Interactively prompts for and saves the Groq API key
    to ~/.devbase/config.toml for persistent use.
    """
    import toml
    from devbase.utils.paths import get_devbase_dir, get_config_path
    
    root: Path = ctx.obj["root"]
    config_dir = get_devbase_dir(root)
    config_file = get_config_path(root)
    
    console.print("\n[bold]🤖 AI Configuration[/bold]\n")
    console.print("This command configures your Groq API key for AI features.")
    console.print("Get your API key at: [cyan]https://console.groq.com/keys[/cyan]\n")
    
    # Load existing config if present
    existing_config: dict = {}
    if config_file.exists():
        try:
            existing_config = toml.load(config_file)
        except Exception:
            pass
    
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
    
    if not api_key:
        console.print("[yellow]⚠[/yellow] No API key entered. Configuration unchanged.")
        raise typer.Exit(0)
    
    # Create config directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Update config
    if "ai" not in existing_config:
        existing_config["ai"] = {}
    existing_config["ai"]["groq_api_key"] = api_key
    
    # Save config
    try:
        with open(config_file, "w") as f:
            toml.dump(existing_config, f)
        
        try:
            config_file.chmod(0o600)
        except Exception:
            pass
        
        console.print(f"\n[green]✓[/green] API key saved to: [cyan]{config_file}[/cyan]")
        
        # Test connection
        console.print("\n[dim]Testing connection...[/dim]")
        try:
            provider = _get_provider()
            provider.validate_connection()
            console.print("[green]✓[/green] Connection successful! AI features are ready.")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Connection test failed: {e}")
    
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to save configuration: {e}")
        raise typer.Exit(1)


@app.command()
def organize(
    path: Annotated[str, typer.Argument(help="File to organize")],
    auto: Annotated[
        bool,
        typer.Option("--auto", "-a", help="Move file automatically without confirmation"),
    ] = False,
    ctx: typer.Context = None,
) -> None:
    """Suggest organization for a file using AI."""
    from devbase.ai.exceptions import DevBaseAIError
    
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]✗[/red] File not found: {path}")
        raise typer.Exit(1)
    
    workspace_root = ctx.obj.get("root") if ctx and ctx.obj else None
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        progress.add_task(description="🤖 Analyzing file...", total=None)
        try:
            service = _get_service()
            suggestion = service.suggest_organization(str(file_path), workspace_root=workspace_root)
        except DevBaseAIError as e:
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
    if auto:
        console.print("\n[yellow]⚠[/yellow] Auto-move not implemented yet.")
    else:
        console.print("\n[dim]Use --auto to move the file automatically.[/dim]")


@app.command()
def insights(
    path: Annotated[Optional[str], typer.Option("--path", "-p", help="Directory to analyze")] = None,
    ctx: typer.Context = None,
) -> None:
    """Generate insights about workspace structure."""
    from devbase.ai.exceptions import DevBaseAIError
    
    workspace_path = Path(path) if path else (ctx.obj["root"] if ctx and ctx.obj and ctx.obj.get("root") else Path.cwd())
    if not workspace_path.exists():
        console.print(f"[red]✗[/red] Path not found: {workspace_path}")
        raise typer.Exit(1)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        progress.add_task(description="🔍 Analyzing workspace structure...", total=None)
        try:
            service = _get_service()
            analysis = service.generate_insights(str(workspace_path))
        except DevBaseAIError as e:
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


@app.command()
def status() -> None:
    """Check AI provider configuration status."""
    console.print("\n[bold]🤖 AI Status[/bold]\n")
    env_key = os.environ.get("GROQ_API_KEY", "")
    if env_key:
        masked = env_key[:8] + "..." + env_key[-4:] if len(env_key) > 12 else "****"
        console.print(f"[green]✓[/green] GROQ_API_KEY env var: [dim]{masked}[/dim]")
    else:
        console.print("[dim]✗[/dim] GROQ_API_KEY env var: not set")
    
    from devbase.utils.paths import get_config_path
    root: Path = ctx.obj["root"]
    config_file = get_config_path(root)
    if config_file.exists():
        try:
            import toml
            config = toml.load(config_file)
            config_key = config.get("ai", {}).get("groq_api_key", "")
            if config_key:
                masked = config_key[:8] + "..." + config_key[-4:] if len(config_key) > 12 else "****"
                console.print(f"[green]✓[/green] Config file key: [dim]{masked}[/dim]")
            else:
                console.print("[dim]✗[/dim] Config file key: not set")
        except Exception:
            console.print("[yellow]⚠[/yellow] Config file: parse error")
    else:
        console.print(f"[dim]✗[/dim] Config file not found")
    
    console.print("\n[dim]Testing connection...[/dim]")
    try:
        provider = _get_provider()
        provider.validate_connection()
        console.print("[green]✓[/green] Connection: OK")
        console.print(f"[green]✓[/green] Model: {provider.model}")
    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")


@app.command("index")
def index(
    rebuild: Annotated[bool, typer.Option("--rebuild", help="Force rebuild of entire index")] = False,
    ctx: typer.Context = None,
) -> None:
    """🔍 Index workspace for semantic search."""
    try:
        from devbase.services.search_engine import SearchEngine
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

    engine = SearchEngine()
    root = ctx.obj["root"] if ctx and ctx.obj and ctx.obj.get("root") else Path.cwd()
    
    with console.status("[bold blue]Indexing workspace...[/bold blue]"):
        try:
            engine.rebuild_index(root)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    console.print("[green]✓[/green] Indexing complete.")


@app.command("chat")
def chat(
    prompt: Annotated[str, typer.Argument(help="Message to AI")],
    model: Annotated[Optional[str], typer.Option("--model", "-m", help="Provider model")] = None,
    temperature: Annotated[float, typer.Option("--temp", "-t", help="Creativity (0.0-1.0)")] = 0.5,
) -> None:
    """💬 Chat with your workspace using RAG."""
    provider = _get_provider()
    
    # Try RAG Retrieval
    context = ""
    try:
        from devbase.services.search_engine import SearchEngine
        engine = SearchEngine()
        with console.status("[bold blue]Retrieving context...[/bold blue]"):
             results = engine.search(prompt, limit=3)
             if results:
                 context = "\n\n".join([f"Source: {r.file_path}\n{r.content}" for r in results])
                 console.print(f"[dim]Found {len(results)} relevant context chunks.[/dim]")
    except Exception:
        pass

    final_prompt = prompt
    if context:
        final_prompt = f"Use the following context to answer the user's question.\nContext:\n{context}\n\nQuestion: {prompt}"

    with console.status("[bold blue]Thinking...[/bold blue]"):
        try:
            # We assume provider has a generate method (re-mapped from complete in some versions)
            # or we use complete directly. GroqProvider uses complete.
            try:
                response_text = provider.complete(final_prompt, temperature=temperature)
            except AttributeError:
                # Fallback to generate if implemented in some PRs
                response = provider.generate(final_prompt, temperature=temperature)
                response_text = response.content
            
            console.print()
            console.print(Panel(response_text, title="[bold green]🤖 AI Response[/bold green]", border_style="green"))
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


@app.command("classify")
def classify(
    text: Annotated[str, typer.Argument(help="Text to classify")],
    categories: Annotated[str, typer.Option("--categories", "-c", help="Comma-separated list")] = "feature,bug,docs,chore,refactor",
) -> None:
    """🏷️ Classify text into a category."""
    provider = _get_provider()
    category_list = [c.strip() for c in categories.split(",")]
    with console.status("[bold blue]Classifying...[/bold blue]"):
        try:
            # Note: provider.classify might be expected by some PRs
            result = provider.complete(f"Classify this text into one of [{','.join(category_list)}]: {text}\n\nCategory:")
            console.print(f"\n[bold green]Category:[/bold green] {result.strip()}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


@app.command("summarize")
def summarize(
    text: Annotated[str, typer.Argument(help="Text to summarize")],
    max_length: Annotated[int, typer.Option("--max-length", "-l")] = 50,
) -> None:
    """📝 Summarize text."""
    provider = _get_provider()
    with console.status("[bold blue]Summarizing...[/bold blue]"):
        try:
            result = provider.complete(f"Summarize this text in max {max_length} words: {text}")
            console.print(f"\n[bold green]Summary:[/bold green]\n{result.strip()}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


@routine_app.command("briefing")
def briefing() -> None:
    """🌅 Daily morning briefing."""
    try:
        from devbase.services.routine_agent import RoutineAgent
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

    agent = RoutineAgent()
    pending = agent.get_yesterday_pending()
    console.print()
    console.print(Panel("\n".join([f"- {task}" for task in pending]), title="[bold yellow]🌅 Morning Briefing: Pending Tasks[/bold yellow]", border_style="yellow"))


@routine_app.command("triage")
def triage(
    apply: Annotated[bool, typer.Option("--apply", help="Automatically move files")] = False,
) -> None:
    """📥 Inbox triage and classification."""
    from rich.prompt import Confirm
    try:
        from devbase.services.routine_agent import RoutineAgent
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

    agent = RoutineAgent()
    files = agent.scan_inbox()
    if not files:
        console.print("[green]Inbox is empty! 🎉[/green]")
        return

    for file_path in files:
        console.print(f"📄 [bold]{file_path.name}[/bold]")
        try:
            content = file_path.read_text(encoding="utf-8")
            with console.status("  Analyzing..."):
                result = agent.classify_inbox_item(content)
            category = result["category"]
            console.print(f"  ➜ Suggested: [cyan]{category}[/cyan]")
            if apply or Confirm.ask(f"  Move to {category}?", default=False):
                if agent.move_to_category(file_path, category):
                    console.print(f"  [green]✓ Moved[/green]")
        except Exception as e:
            console.print(f"  [red]✗ Error: {e}[/red]")
        console.print()
