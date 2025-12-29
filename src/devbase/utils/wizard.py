"""
Interactive Setup Wizard
=========================
Guided setup experience for first-time users.
Implements Solution #4 from Usability Simplification Plan.

Features:
- Welcome screen with project overview
- Prerequisite checking (Python, Git)
- Workspace location selection with validation
- Module selection (PKM, AI, Operations)
- Air-Gap configuration
- Post-install success message
"""
import subprocess
import sys
from pathlib import Path

from devbase import __version__

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


def check_python_version() -> tuple[bool, str]:
    """
    Check if Python version meets minimum requirements (>=3.8).
    
    Returns:
        tuple: (is_valid, message)
    """
    current = sys.version_info
    required = (3, 8)

    if current >= required:
        return True, f"✅ Python {current.major}.{current.minor}.{current.micro}"
    else:
        return False, (
            f"❌ Python {current.major}.{current.minor} detected\n"
            f"   Required: Python 3.8+\n"
            f"   Install: https://www.python.org/downloads/"
        )


def check_git_installed() -> tuple[bool, str]:
    """
    Check if Git is installed and accessible.
    
    Returns:
        tuple: (is_installed, message)
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        version = result.stdout.strip()
        return True, f"✅ {version}"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False, (
            "❌ Git not found\n"
            "   Install: https://git-scm.com/downloads"
        )


def run_prerequisite_checks() -> bool:
    """
    Run all prerequisite checks and display results.
    
    Returns:
        bool: True if all checks pass
    """
    console.print()
    console.print("[bold cyan]Checking prerequisites...[/bold cyan]\n")

    checks = [
        ("Python", check_python_version()),
        ("Git", check_git_installed()),
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool", style="cyan")
    table.add_column("Status")

    all_passed = True
    for name, (passed, message) in checks:
        table.add_row(name, message)
        if not passed:
            all_passed = False

    console.print(table)
    console.print()

    if not all_passed:
        console.print("[red]⚠️  Some prerequisites are missing.[/red]")
        console.print("[dim]Please install missing tools and try again.[/dim]\n")

    return all_passed


def validate_workspace_path(path: Path) -> tuple[bool, str]:
    """
    Validate proposed workspace path.
    
    Args:
        path: Proposed workspace path
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if path exists and is not a file
    if path.exists() and not path.is_dir():
        return False, "Path exists but is not a directory"

    # Check if path is inside common problematic locations
    problematic = [
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path("/tmp"),
        Path("C:/Windows") if sys.platform == "win32" else None,
    ]

    for problematic_path in problematic:
        if problematic_path and path.is_relative_to(problematic_path):
            return False, f"Not recommended inside {problematic_path}"

    # Check if parent directory exists (or can be created)
    if not path.exists():
        parent = path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create parent directory: {e}"

    return True, ""


def run_interactive_wizard() -> dict:
    """
    Run the complete interactive setup wizard.
    
    Returns:
        dict: Configuration choices made by user
    """
    console.clear()

    # Welcome screen
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🚀 Welcome to DevBase![/bold cyan]\n\n"
        "[white]Your Personal Engineering Operating System[/white]\n\n"
        "This wizard will help you set up your workspace in a few simple steps.",
        border_style="cyan",
        title="DevBase Setup Wizard",
    ))
    console.print()

    console.print("[bold]Step 1/6:[/bold] Checking prerequisites\n")
    if not run_prerequisite_checks():
        raise SystemExit(1)

    console.print("[green]✓ All prerequisites satisfied![/green]\n")
    input("[dim]Press Enter to continue...[/dim]")
    console.clear()

    # Step 2: Workspace Location
    console.print()
    console.print("[bold]Step 2/6:[/bold] Choose workspace location\n")

    default_path = Path.home() / "Dev_Workspace"
    console.print(f"[dim]Recommended: {default_path}[/dim]\n")

    while True:
        workspace_input = Prompt.ask(
            "[bold]Workspace location[/bold]",
            default=str(default_path)
        )

        workspace_path = Path(workspace_input).expanduser().resolve()
        is_valid, error = validate_workspace_path(workspace_path)

        if is_valid:
            break
        else:
            console.print(f"[red]✗ {error}[/red]")
            console.print("[dim]Please choose a different location.[/dim]\n")

    console.print(f"\n[green]✓[/green] Workspace: [cyan]{workspace_path}[/cyan]\n")

    # Step 3: Module Selection
    console.print("[bold]Step 3/6:[/bold] Select modules to install\n")

    modules = {
        "pkm": Confirm.ask(
            "📚 [bold]PKM[/bold] (Personal Knowledge Management - notes, ADRs, TIL)",
            default=True
        ),
        "ai": Confirm.ask(
            "🤖 [bold]AI[/bold] (Local AI tools and model management)",
            default=False
        ),
        "operations": Confirm.ask(
            "🔧 [bold]Operations[/bold] (Automation, backups, monitoring)",
            default=True
        ),
    }

    console.print()
    enabled = [name.upper() for name, enabled in modules.items() if enabled]
    console.print(f"[green]✓[/green] Modules: {', '.join(enabled) if enabled else 'Core only'}\n")

    # Step 4: Air-Gap Configuration
    console.print("[bold]Step 4/6:[/bold] Security configuration\n")

    console.print("[dim]Air-Gap protection prevents private vault from syncing to cloud.[/dim]\n")
    airgap = Confirm.ask(
        "🔒 Enable Air-Gap protection for [yellow]12_private_vault[/yellow]?",
        default=True
    )

    console.print(f"\n[green]✓[/green] Air-Gap: {'Enabled ✓' if airgap else 'Disabled'}\n")

    # Step 5: Development Environment
    console.print("[bold]Step 5/6:[/bold] Development Environment\n")

    git_init = Confirm.ask(
        "🐙 Initialize [bold]Git[/bold] repository?",
        default=True
    )

    vscode_config = Confirm.ask(
        "📝 Configure [bold]VS Code[/bold] workspace settings?",
        default=True
    )
    
    console.print(f"\n[green]✓[/green] Environment: {'Git, ' if git_init else ''}{'VS Code' if vscode_config else ''}\n")

    # Step 6: Confirmation
    console.print("[bold]Step 6/6:[/bold] Review and confirm\n")

    summary = Table(show_header=False, box=None)
    summary.add_column("Setting", style="cyan")
    summary.add_column("Value", style="white")

    summary.add_row("Workspace", str(workspace_path))
    summary.add_row("Modules", ", ".join(enabled) if enabled else "Core only")
    summary.add_row("Air-Gap", "Enabled" if airgap else "Disabled")
    summary.add_row("Git Init", "Yes" if git_init else "No")
    summary.add_row("VS Code", "Yes" if vscode_config else "No")

    console.print(summary)
    console.print()

    if not Confirm.ask("[bold]Proceed with setup?[/bold]", default=True):
        console.print("[yellow]Setup cancelled.[/yellow]")
        raise SystemExit(0)

    return {
        "path": workspace_path,
        "modules": modules,
        "airgap": airgap,
        "git_init": git_init,
        "vscode_config": vscode_config,
    }


def execute_setup_with_config(config: dict) -> None:
    """
    Execute setup with wizard configuration.
    
    Args:
        config: Configuration from wizard
    """
    console.print()
    console.print("[bold cyan]Creating workspace...[/bold cyan]\n")

    # Import setup modules from core (where stubs are defined)
    from devbase.utils.filesystem import get_filesystem
    from devbase.utils.state import get_state_manager
    from devbase.commands.core import (
        run_setup_ai,
        run_setup_code,
        run_setup_core,
        run_setup_operations,
        run_setup_pkm,
    )

    root = config["path"]
    fs = get_filesystem(str(root), dry_run=False)

    # Setup modules based on selection
    setup_tasks = [
        ("Core Structure", run_setup_core, True),  # Always run
        ("Knowledge Management", run_setup_pkm, config["modules"]["pkm"]),
        ("Code Templates", run_setup_code, True),  # Always run
        ("AI Integration", run_setup_ai, config["modules"]["ai"]),
        ("Operations", run_setup_operations, config["modules"]["operations"]),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for name, run_func, enabled in setup_tasks:
            if not enabled:
                continue

            task = progress.add_task(f"Setting up {name}...", total=None)
            try:
                run_func(fs, policy_version="4.0")
                progress.update(task, description=f"[green]✓[/green] {name}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] {name}")
                console.print(f"[red]Error: {e}[/red]")
                raise

    # Update state via adapter
    state_mgr = get_state_manager(root)
    from datetime import datetime

    state = state_mgr.get_state()
    state["version"] = __version__
    state["policyVersion"] = "4.0"
    state["installedAt"] = datetime.now().isoformat()
    state["lastUpdate"] = state["installedAt"]
    state["modules"] = [name for name, _, enabled in setup_tasks if enabled]
    state_mgr.save_state(state)

    # Git Initialization
    if config.get("git_init"):
        console.print("\n[bold]Initializing Git repository...[/bold]")
        try:
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "commit", "-m", "chore: initial workspace setup"], check=True, capture_output=True)
            console.print("  [green]✓[/green] Git initialized and initial commit created")
        except Exception as e:
            console.print(f"  [red]✗[/red] Git init failed: {e}")

    # VS Code Configuration
    if config.get("vscode_config"):
        console.print("\n[bold]Configuring VS Code...[/bold]")
        vscode_dir = root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        settings = vscode_dir / "settings.json"
        if not settings.exists():
            settings.write_text('{\n    "files.exclude": {\n        "**/__pycache__": true,\n        "**/.DS_Store": true\n    },\n    "editor.formatOnSave": true,\n    "python.analysis.typeCheckingMode": "basic"\n}', encoding="utf-8")
        
        extensions = vscode_dir / "extensions.json"
        if not extensions.exists():
            extensions.write_text('{\n    "recommendations": [\n        "ms-python.python",\n        "tamasfe.even-better-toml",\n        "yzhang.markdown-all-in-one"\n    ]\n}', encoding="utf-8")
            
        console.print("  [green]✓[/green] .vscode settings created")

    # Success message
    console.print()
    console.print(Panel.fit(
        "[bold green]✅ Setup Complete![/bold green]\n\n"
        f"Your workspace is ready at:\n[cyan]{root}[/cyan]\n\n"
        "[bold]Next steps:[/bold]\n"
        f"  1. [cyan]cd {root}[/cyan]\n"
        "  2. [cyan]devbase core doctor[/cyan]  [dim](verify installation)[/dim]\n"
        "  3. [cyan]devbase dev new my-project[/cyan]  [dim](create first project)[/dim]",
        border_style="green",
        title="🎉 Success",
    ))
    console.print()
