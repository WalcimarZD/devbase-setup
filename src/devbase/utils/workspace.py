"""
Workspace Detection Utility
============================
Auto-detects DevBase workspace root by searching for .devbase_state.json.
Implements Solution #1 from Usability Simplification Plan.

Search Strategy:
1. Current directory
2. Parent directories (walk up tree)
3. Environment variable $DEVBASE_ROOT
4. Default location: ~/Dev_Workspace
5. Interactive setup if none found
"""
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()


def detect_workspace_root() -> Path:
    """
    Auto-detect DevBase workspace root.
    
    Returns:
        Path: Resolved absolute path to workspace root
        
    Raises:
        typer.Exit: If no workspace found and user declines setup
    """
    # Strategy 1: Walk up from current directory
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        state_file = parent / ".devbase_state.json"
        if state_file.exists():
            console.print(f"[dim]✓ Detected workspace: {parent}[/dim]")
            return parent

    # Strategy 2: Check environment variable
    env_root = os.environ.get("DEVBASE_ROOT")
    if env_root:
        env_path = Path(env_root).expanduser().resolve()
        if (env_path / ".devbase_state.json").exists():
            console.print(f"[dim]✓ Using $DEVBASE_ROOT: {env_path}[/dim]")
            return env_path

    # Strategy 3: Check default location
    default = Path.home() / "Dev_Workspace"
    if (default / ".devbase_state.json").exists():
        console.print(f"[dim]✓ Using default workspace: {default}[/dim]")
        return default

    # Strategy 4: No workspace found - prompt for setup
    return prompt_workspace_setup()


def prompt_workspace_setup() -> Path:
    """
    Interactive prompt when no workspace is detected.
    
    Offers to create new workspace or specify existing location.
    
    Returns:
        Path: User-specified or default workspace path
    """
    console.print()
    console.print(Panel.fit(
        "[bold yellow]⚠️  No DevBase workspace detected[/bold yellow]\n\n"
        "A workspace is required to use DevBase commands.\n"
        "You can create a new workspace or specify an existing one.",
        border_style="yellow"
    ))
    console.print()

    # Ask if user wants to create workspace now
    create_now = Confirm.ask(
        "Would you like to create a workspace now?",
        default=True
    )

    if not create_now:
        console.print("[yellow]Run 'devbase setup' when ready to create a workspace.[/yellow]")
        raise SystemExit(0)

    # Get workspace location
    default_path = Path.home() / "Dev_Workspace"
    workspace_input = Prompt.ask(
        "[bold]Workspace location[/bold]",
        default=str(default_path)
    )

    workspace_path = Path(workspace_input).expanduser().resolve()

    # Validate path
    if workspace_path.exists() and not workspace_path.is_dir():
        console.print("[red]Error: Path exists but is not a directory![/red]")
        raise SystemExit(1)

    console.print(f"\n[green]✓[/green] Workspace will be created at: [cyan]{workspace_path}[/cyan]")
    console.print("[dim]Run 'devbase setup' to initialize the workspace structure.[/dim]\n")

    return workspace_path


def is_valid_workspace(path: Path) -> bool:
    """
    Check if a path is a valid DevBase workspace.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if path contains .devbase_state.json
    """
    return (path / ".devbase_state.json").exists()


def get_workspace_areas(root: Path) -> dict[str, Path]:
    """
    Get paths to all Johnny.Decimal areas in workspace.
    
    Args:
        root: Workspace root path
        
    Returns:
        dict: Mapping of area names to paths
    """
    return {
        "system": root / "00-09_SYSTEM",
        "knowledge": root / "10-19_KNOWLEDGE",
        "code": root / "20-29_CODE",
        "operations": root / "30-39_OPERATIONS",
        "media": root / "40-49_MEDIA_ASSETS",
        "archive": root / "90-99_ARCHIVE_COLD",
    }


def get_semantic_locations(root: Path) -> dict[str, Path]:
    """
    Get semantic shortcuts for common locations (for 'goto' command).
    
    Args:
        root: Workspace root path
        
    Returns:
        dict: Mapping of semantic names to paths
    """
    return {
        "code": root / "20-29_CODE" / "21_monorepo_apps",
        "packages": root / "20-29_CODE" / "22_monorepo_packages",
        "knowledge": root / "10-19_KNOWLEDGE" / "11_public_garden",
        "vault": root / "10-19_KNOWLEDGE" / "12_private_vault",
        "ai": root / "30-39_OPERATIONS" / "30_ai",
        "backups": root / "30-39_OPERATIONS" / "31_backups",
        "inbox": root / "00-09_SYSTEM" / "00_inbox",
        "templates": root / "00-09_SYSTEM" / "05_templates",
        "dotfiles": root / "00-09_SYSTEM" / "01_dotfiles",
    }
