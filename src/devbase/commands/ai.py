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
from typing import Optional

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
    
    # Save config with restrictive permissions
    try:
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
