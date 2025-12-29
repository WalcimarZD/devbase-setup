"""
AI Commands: organize, insights, config
=========================================
AI-powered commands for workspace management.

Commands:
    devbase ai organize <path>  - Suggest file organization
    devbase ai insights         - Generate workspace insights
    devbase ai config           - Configure AI provider API key
"""
from pathlib import Path

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


<<<<<<< HEAD
@app.command("chat")
def chat(
    prompt: Annotated[
        str,
        typer.Argument(help="Your message or question"),
    ],
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Model to use (default: llama-3.1-8b-instant)"),
    ] = None,
    temperature: Annotated[
        float,
        typer.Option("--temperature", "-t", help="Creativity level (0.0-2.0)"),
    ] = 0.7,
) -> None:
    """
    💬 Chat with AI assistant.

    Send a prompt and get a response from the configured LLM.

    Examples:
        devbase ai chat "Explain SOLID principles briefly"
        devbase ai chat "Suggest a project name for a REST API" -t 1.0
    """
    provider = _get_provider()

=======
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
    
    Example:
        devbase ai config
    """
    import toml
    
    config_dir = Path.home() / ".devbase"
    config_file = config_dir / "config.toml"
    
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
    
    # Validate key format (Groq keys start with 'gsk_')
    if not api_key.startswith("gsk_"):
        console.print(
            "[yellow]⚠[/yellow] This doesn't look like a Groq API key "
            "(should start with 'gsk_'). Saving anyway..."
        )
    
    # Create config directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Update config
    if "ai" not in existing_config:
        existing_config["ai"] = {}
    existing_config["ai"]["groq_api_key"] = api_key
    
<<<<<<< HEAD
>>>>>>> origin/main
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
    except Exception as e:
<<<<<<< HEAD
        # Don't fail chat if search fails, but surface the issue for visibility
        console.print(f"[dim yellow]Search unavailable: {e}[/dim yellow]")
=======
        # Don't fail chat if search fails
        # console.print(f"[dim yellow]Search unavailable: {e}[/dim yellow]")
        pass
>>>>>>> origin/main

    # Inject context
    final_prompt = prompt
    if context:
        final_prompt = f"""Use the following context to answer the user's question.
If the context is not relevant, ignore it.

Context:
{context}

Question:
{prompt}"""

    with console.status("[bold blue]Thinking...[/bold blue]"):
        try:
            response = provider.generate(
                final_prompt,
                model=model,
                temperature=temperature,
            )
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Display response in a nice panel
    console.print()
    console.print(Panel(
        response.content,
        title="[bold green]🤖 AI Response[/bold green]",
        subtitle=f"[dim]{response.model} | {response.tokens_used} tokens | {response.latency_ms:.0f}ms[/dim]",
        border_style="green",
    ))


@app.command("index")
def index(
    rebuild: Annotated[
        bool,
        typer.Option("--rebuild", help="Force rebuild of entire index"),
    ] = False,
) -> None:
    """
    🔍 Index workspace for semantic search.

    Generates embeddings for files in KNOWLEDGE and CODE areas.
    """
    try:
        from devbase.services.search_engine import SearchEngine
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

    engine = SearchEngine()

    with console.status("[bold blue]Indexing workspace...[/bold blue]"):
        try:
            # We assume current directory as root for now, or pass configured root
            # Access context object if we could, but here we keep it simple
            engine.rebuild_index(Path.cwd())
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print("[green]✓[/green] Indexing complete.")


@app.command("classify")
def classify(
    text: Annotated[
        str,
        typer.Argument(help="Text to classify"),
    ],
    categories: Annotated[
        str,
        typer.Option("--categories", "-c", help="Comma-separated list of categories"),
    ] = "feature,bug,docs,chore,refactor",
) -> None:
    """
    🏷️ Classify text into a category.

    Uses AI to classify text into one of the provided categories.

    Examples:
        devbase ai classify "Fix login button not working" -c "bug,feature,docs"
        devbase ai classify "Add dark mode support"
    """
    provider = _get_provider()
    category_list = [c.strip() for c in categories.split(",")]

    with console.status("[bold blue]Classifying...[/bold blue]"):
        try:
            result = provider.classify(text, category_list)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Display result
    console.print()
    console.print(f"[bold]Text:[/bold] {text[:100]}{'...' if len(text) > 100 else ''}")
    console.print(f"[bold green]Category:[/bold green] {result}")


@app.command("summarize")
def summarize(
    text: Annotated[
        str,
        typer.Argument(help="Text to summarize"),
    ],
    max_length: Annotated[
        int,
        typer.Option("--max-length", "-l", help="Maximum summary length in words"),
    ] = 50,
) -> None:
    """
    📝 Summarize text.

    Uses AI to create a concise summary of the provided text.

    Examples:
        devbase ai summarize "Long text here..." -l 30
    """
    provider = _get_provider()

    with console.status("[bold blue]Summarizing...[/bold blue]"):
        try:
            result = provider.summarize(text, max_length=max_length)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Display result
    console.print()
    console.print(Panel(
        result,
        title="[bold green]📝 Summary[/bold green]",
        border_style="green",
    ))


@app.command("status")
def status() -> None:
    """
    📊 Check AI worker status.

    Shows the current state of the background AI worker
    and pending tasks in the queue.
    """
=======
    # Save config with restrictive permissions
>>>>>>> origin/main
    try:
<<<<<<< HEAD
        from devbase.adapters.storage.duckdb_adapter import get_connection
        from devbase.services.async_worker import get_worker
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

    # Check worker status
    worker = get_worker()
    worker_status = "🟢 Running" if worker.is_running() else "🔴 Stopped"

    # Check queue
    try:
        conn = get_connection()
        result = conn.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'processing') as processing,
                COUNT(*) FILTER (WHERE status = 'done') as done,
                COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM ai_task_queue
        """).fetchone()

        pending, processing, done, failed = result if result else (0, 0, 0, 0)
    except Exception:
        pending, processing, done, failed = 0, 0, 0, 0

    # Display status
    table = Table(title="AI Worker Status")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Worker", worker_status)
    table.add_row("Pending Tasks", str(pending))
    table.add_row("Processing", str(processing))
    table.add_row("Completed", str(done))
    table.add_row("Failed", str(failed))

    console.print()
    console.print(table)

    # Tips
    if not worker.is_running():
        console.print()
        console.print("[dim]💡 Tip: Set ai.enabled=true in config to auto-start worker[/dim]")
=======
        with open(config_file, "w") as f:
            toml.dump(existing_config, f)
        
        # Set restrictive permissions (owner-only read/write)
        # This works on Unix; on Windows, permissions are handled differently
        try:
            config_file.chmod(0o600)
        except Exception:
            pass  # Ignore permission errors on Windows
        
        console.print(f"\n[green]✓[/green] API key saved to: [cyan]{config_file}[/cyan]")
        
        # Test connection
        console.print("\n[dim]Testing connection...[/dim]")
        try:
            from devbase.ai.providers.groq import GroqProvider
            provider = GroqProvider(api_key=api_key)
            provider.validate_connection()
            console.print("[green]✓[/green] Connection successful! AI features are ready.")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Connection test failed: {e}")
            console.print("The key was saved, but please verify it's correct.")
    
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
    """Suggest organization for a file using AI.
    
    Analyzes the file and suggests the best location within
    the Johnny.Decimal workspace structure.
    
    Examples:
        devbase ai organize inbox/document.pdf
        devbase ai organize notes.md --auto
    """
    from devbase.ai.exceptions import DevBaseAIError
    
    file_path = Path(path)
    if not file_path.exists():
        console.print(f"[red]✗[/red] File not found: {path}")
        raise typer.Exit(1)
    
    # Get workspace root from context
    workspace_root = None
    if ctx and ctx.obj:
        workspace_root = ctx.obj.get("root")
    
    console.print()
    
    # Show spinner while analyzing
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="🤖 Analyzing file...", total=None)
        
        try:
            service = _get_service()
            suggestion = service.suggest_organization(
                str(file_path),
                workspace_root=workspace_root,
            )
        except DevBaseAIError as e:
            console.print(f"[red]✗[/red] AI analysis failed: {e}")
            raise typer.Exit(1)
    
    # Display suggestion in a nice panel
    confidence_emoji = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.5 else "🔴"
    confidence_pct = int(suggestion.confidence * 100)
    
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Label", style="dim")
    table.add_column("Value")
    
    table.add_row("Destination:", f"[cyan]{suggestion.destination}[/cyan]")
    if suggestion.new_name:
        table.add_row("New Name:", f"[cyan]{suggestion.new_name}[/cyan]")
    table.add_row("Confidence:", f"{confidence_emoji} {confidence_pct}%")
    table.add_row("", "")
    table.add_row("Reasoning:", suggestion.reasoning)
    
    console.print(Panel(
        table,
        title="[bold]📁 Organization Suggestion[/bold]",
        border_style="blue",
    ))
    
    # Handle auto-move or prompt
    if auto:
        console.print("\n[yellow]⚠[/yellow] Auto-move not implemented yet.")
        # TODO: Implement file moving logic
    else:
        console.print("\n[dim]Use --auto to move the file automatically.[/dim]")
>>>>>>> origin/main


@app.command()
def insights(
    path: Annotated[
        Optional[str],
        typer.Option("--path", "-p", help="Directory to analyze"),
    ] = None,
    ctx: typer.Context = None,
) -> None:
    """Generate insights about workspace structure.
    
    Analyzes the workspace organization and provides
    actionable recommendations for improvement.
    
    Examples:
        devbase ai insights
        devbase ai insights --path ./my-workspace
    """
<<<<<<< HEAD
    🚀 Start the AI background worker.

    Starts the daemon thread that processes queued AI tasks.
=======
    from devbase.ai.exceptions import DevBaseAIError
    
    # Determine workspace path
    if path:
        workspace_path = Path(path)
    elif ctx and ctx.obj and ctx.obj.get("root"):
        workspace_path = ctx.obj["root"]
    else:
        workspace_path = Path.cwd()
    
    if not workspace_path.exists():
        console.print(f"[red]✗[/red] Path not found: {workspace_path}")
        raise typer.Exit(1)
    
    console.print()
    
    # Show spinner while analyzing
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="🔍 Analyzing workspace structure...", total=None)
        
        try:
            service = _get_service()
            analysis = service.generate_insights(str(workspace_path))
        except DevBaseAIError as e:
            console.print(f"[red]✗[/red] AI analysis failed: {e}")
            raise typer.Exit(1)
    
    # Display header with score
    score_emoji = "🟢" if analysis.score >= 80 else "🟡" if analysis.score >= 60 else "🔴"
    
    console.print(Panel(
        f"[bold]{score_emoji} Organization Score: {analysis.score}/100[/bold]",
        title="[bold]📊 Workspace Analysis[/bold]",
        border_style="blue",
    ))
    
    if not analysis.insights:
        console.print("\n[green]✓[/green] No significant issues found!")
        return
    
<<<<<<< HEAD
    worker.start()
    console.print("[green]✓[/green] AI worker started")


# Routine commands
routine_app = typer.Typer(
    name="routine",
    help="📅 Routine management (briefing, triage)",
    no_args_is_help=True,
)
app.add_typer(routine_app, name="routine")


@routine_app.command("briefing")
def briefing() -> None:
    """
    🌅 Daily briefing.

    Shows pending tasks from yesterday's daybook.
>>>>>>> origin/main
    """
    try:
        from devbase.services.routine_agent import RoutineAgent
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

<<<<<<< HEAD
    worker = get_worker()

    if worker.is_running():
        console.print("[yellow]Worker is already running[/yellow]")
        return

    worker.start()
    console.print("[green]✓[/green] AI worker started")


# Routine commands
routine_app = typer.Typer(
    name="routine",
    help="📅 Routine management (briefing, triage)",
    no_args_is_help=True,
)
app.add_typer(routine_app, name="routine")


@routine_app.command("briefing")
def briefing() -> None:
    """
    🌅 Daily briefing.

    Shows pending tasks from yesterday's daybook.
    """
    try:
        from devbase.services.routine_agent import RoutineAgent
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)

    agent = RoutineAgent()
    pending = agent.get_yesterday_pending()

    console.print()
    console.print(Panel(
        "\n".join([f"- {task}" for task in pending]),
        title="[bold yellow]🌅 Morning Briefing: Pending Tasks[/bold yellow]",
        border_style="yellow",
    ))


@routine_app.command("triage")
def triage(
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Automatically move files to suggested categories"),
    ] = False,
) -> None:
    """
    📥 Inbox triage.

    Scans Inbox and suggests JD categories.
    Use --apply to move files automatically.
    """
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

=======
    agent = RoutineAgent()
    pending = agent.get_yesterday_pending()

    console.print()
    console.print(Panel(
        "\n".join([f"- {task}" for task in pending]),
        title="[bold yellow]🌅 Morning Briefing: Pending Tasks[/bold yellow]",
        border_style="yellow",
    ))


@routine_app.command("triage")
def triage(
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Automatically move files to suggested categories"),
    ] = False,
) -> None:
    """
    📥 Inbox triage.

    Scans Inbox and suggests JD categories.
    Use --apply to move files automatically.
    """
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

>>>>>>> origin/main
    console.print(f"[bold]Found {len(files)} items in Inbox:[/bold]")
    console.print()

    for file_path in files:
        console.print(f"📄 [bold]{file_path.name}[/bold]")

        # Read content (text only)
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            console.print("  [dim]Skipping (binary or non-text)[/dim]")
            continue

        with console.status("  Analyzing..."):
            result = agent.classify_inbox_item(content)

        category = result["category"]
        confidence = result.get("confidence", "unknown")

        console.print(f"  ➜ Suggested: [cyan]{category}[/cyan] [dim]({confidence})[/dim]")

        should_move = False
        if apply:
            should_move = True
        else:
            should_move = Confirm.ask(f"  Move to {category}?", default=False)

        if should_move:
            new_path = agent.move_to_category(file_path, category)
            if new_path:
                console.print(f"  [green]✓ Moved to {new_path}[/green]")
            else:
                console.print("  [red]✗ Failed to move[/red]")
        else:
            console.print("  [dim]Skipped[/dim]")

        console.print()
<<<<<<< HEAD
=======
=======
    # Display insights as markdown
    console.print("\n[bold]### Insights[/bold]\n")
    
    severity_icons = {
        "warning": "⚠️",
        "suggestion": "💡",
        "info": "ℹ️",
    }
    
    for insight in analysis.insights:
        icon = severity_icons.get(insight.severity, "•")
        category_color = {
            "architecture": "magenta",
            "optimization": "cyan",
            "organization": "green",
        }.get(insight.category, "white")
        
        console.print(f"{icon} [bold]{insight.title}[/bold]")
        console.print(f"   [dim][{category_color}]{insight.category}[/{category_color}][/dim]")
        console.print(f"   {insight.description}")
        console.print()


@app.command()
def status() -> None:
    """Check AI provider configuration status.
    
    Displays the current AI configuration and tests
    the connection to verify everything is working.
    
    Example:
        devbase ai status
    """
    import os
    
    console.print("\n[bold]🤖 AI Status[/bold]\n")
    
    # Check environment variable
    env_key = os.environ.get("GROQ_API_KEY", "")
    if env_key:
        masked = env_key[:8] + "..." + env_key[-4:] if len(env_key) > 12 else "****"
        console.print(f"[green]✓[/green] GROQ_API_KEY env var: [dim]{masked}[/dim]")
    else:
        console.print("[dim]✗[/dim] GROQ_API_KEY env var: not set")
    
    # Check config file
    config_file = Path.home() / ".devbase" / "config.toml"
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
        console.print(f"[dim]✗[/dim] Config file: {config_file} not found")
    
    # Test connection
    console.print("\n[dim]Testing connection...[/dim]")
    try:
        provider = _get_provider()
        provider.validate_connection()
        console.print("[green]✓[/green] Connection: OK")
        console.print(f"[green]✓[/green] Model: {provider.model}")
    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
>>>>>>> origin/main
>>>>>>> origin/main
