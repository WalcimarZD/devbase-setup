"""
AI Commands - DevBase AI Module CLI
====================================
CLI commands for interacting with AI features.

Commands:
- ai chat: Interactive chat with LLM
- ai classify: Classify text into categories
- ai status: Check AI worker status
- ai process: Force process queued tasks

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

# Initialize Typer app for this command group
app = typer.Typer(
    name="ai",
    help="🧠 AI-powered features (classification, summarization, chat)",
    no_args_is_help=True,
)

console = Console()


def _get_provider():
    """Get LLM provider with proper error handling."""
    try:
        from devbase.adapters.ai.groq_adapter import GroqProvider
        return GroqProvider()
    except ImportError:
        console.print(
            "[red]Error:[/red] Groq SDK not installed. Run: [cyan]uv add groq[/cyan]"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error initializing AI:[/red] {e}")
        console.print(
            "[dim]💡 Tip: Set GROQ_API_KEY environment variable[/dim]"
        )
        raise typer.Exit(1)


@app.command("chat")
def chat(
    prompt: Annotated[
        str,
        typer.Argument(help="Your message or question"),
    ],
    model: Annotated[
        Optional[str],
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
        # Don't fail chat if search fails
        # console.print(f"[dim yellow]Search unavailable: {e}[/dim yellow]")
        pass

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
    try:
        from devbase.services.async_worker import get_worker
        from devbase.adapters.storage.duckdb_adapter import get_connection
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


@app.command("start")
def start_worker() -> None:
    """
    🚀 Start the AI background worker.
    
    Starts the daemon thread that processes queued AI tasks.
    """
    try:
        from devbase.services.async_worker import get_worker
    except ImportError as e:
        console.print(f"[red]Import error:[/red] {e}")
        raise typer.Exit(1)
    
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
