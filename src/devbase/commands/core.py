"""
Core Commands: setup, doctor, hydrate
======================================
Essential workspace management commands.
"""
# Import legacy modules (will be refactored)
import sys
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "modules" / "python"))

try:
    from filesystem import FileSystem
    from setup_ai import run_setup_ai
    from setup_code import run_setup_code
    from setup_core import run_setup_core
    from setup_operations import run_setup_operations
    from setup_pkm import run_setup_pkm
    from state import StateManager
except ImportError as e:
    print(f"Warning: Could not import legacy modules: {e}")

app = typer.Typer(help="Core workspace commands")
console = Console()

SCRIPT_VERSION = "4.0.0"
POLICY_VERSION = "4.0"


@app.command()
def setup(
    ctx: typer.Context,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing files"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be done without making changes"),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Run interactive setup wizard"),
    ] = True,
) -> None:
    """
    🚀 Initialize or update DevBase workspace structure.
    
    This command creates the complete Johnny.Decimal folder structure,
    governance files, templates, and configuration.
    
    On first run, launches an interactive wizard to guide you through setup.
    """
    root: Path = ctx.obj["root"]

    # Check if this is first-time setup
    state_file = root / ".devbase_state.json"
    is_first_time = not state_file.exists()

    # Run interactive wizard for first-time setup
    if is_first_time and interactive and not dry_run:
        from devbase.utils.wizard import execute_setup_with_config, run_interactive_wizard

        try:
            config = run_interactive_wizard()
            execute_setup_with_config(config)
            return  # Wizard handles everything
        except KeyboardInterrupt:
            console.print("\n[yellow]Setup cancelled by user.[/yellow]")
            raise typer.Exit(0)

    # Standard setup (non-interactive or update)
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]DevBase Setup v{SCRIPT_VERSION}[/bold cyan]\n"
        f"Workspace: [yellow]{root}[/yellow]",
        border_style="cyan"
    ))
    console.print()

    if dry_run:
        console.print("[yellow]⚠️  DRY-RUN MODE: No changes will be made[/yellow]\n")

    # Initialize filesystem
    fs = FileSystem(str(root), dry_run=dry_run)
    state_mgr = StateManager(root)

    # Check existing state
    current_state = state_mgr.get_state()
    if current_state["version"] != "0.0.0":
        console.print(f"[dim]Existing DevBase: v{current_state['version']}[/dim]")
        console.print(f"[dim]Last updated: {current_state['lastUpdate']}[/dim]\n")

    # Execute setup modules with progress
    modules = [
        ("Core Structure", run_setup_core),
        ("Knowledge Management", run_setup_pkm),
        ("Code Templates", run_setup_code),
        ("AI Integration", run_setup_ai),
        ("Operations", run_setup_operations),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for name, run_func in modules:
            task = progress.add_task(f"Setting up {name}...", total=None)
            try:
                # Create minimal UI wrapper for legacy modules
                class LegacyUI:
                    def print_header(self, msg): pass
                    def print_step(self, msg, status):
                        if status == "ERROR":
                            console.print(f"[red]✗ {msg}[/red]")

                run_func(fs, LegacyUI(), policy_version=POLICY_VERSION)
                progress.update(task, description=f"[green]✓[/green] {name}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] {name} - {e}")
                console.print(f"[red]Setup failed: {e}[/red]")
                raise typer.Exit(1)

    # Update state
    if not dry_run:
        new_state = current_state.copy()
        new_state["version"] = SCRIPT_VERSION
        new_state["policyVersion"] = POLICY_VERSION
        new_state["lastUpdate"] = datetime.now().isoformat()
        if not new_state.get("installedAt"):
            new_state["installedAt"] = new_state["lastUpdate"]

        migration_id = f"v{SCRIPT_VERSION}-{datetime.now().strftime('%Y%m%d')}"
        if migration_id not in new_state["migrations"]:
            new_state["migrations"].append(migration_id)

        state_mgr.save_state(new_state)
        console.print("\n[green]✓[/green] State saved")

    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Setup Complete![/bold green]\n\n"
        f"DevBase v{SCRIPT_VERSION} is ready.\n\n"
        "Next steps:\n"
        "  1. [cyan]devbase doctor[/cyan]  - Verify installation\n"
        "  2. [cyan]devbase dev new my-project[/cyan]  - Create first project",
        border_style="green"
    ))


@app.command()
def doctor(
    ctx: typer.Context,
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Auto-fix issues without prompting")] = False,
) -> None:
    """
    🏥 Check workspace health and offer fixes.
    
    Verifies workspace integrity and offers to fix issues interactively.
    Use --fix to auto-fix all issues without prompting.
    """
    from rich.prompt import Confirm
    
    root: Path = ctx.obj["root"]

    console.print()
    console.print("[bold]DevBase Health Check[/bold]")
    console.print(f"[dim]Workspace: {root}[/dim]\n")

    # Collect issues with fix actions
    issues = []
    
    def add_issue(description: str, fix_action=None, fix_description: str = None):
        issues.append({
            "description": description,
            "fix_action": fix_action,
            "fix_description": fix_description or "Auto-fix available"
        })

    # Check areas
    console.print("[bold]Checking folder structure...[/bold]")
    required_areas = [
        '00-09_SYSTEM',
        '10-19_KNOWLEDGE',
        '20-29_CODE',
        '30-39_OPERATIONS',
        '40-49_MEDIA_ASSETS',
        '90-99_ARCHIVE_COLD'
    ]

    for area in required_areas:
        area_path = root / area
        if area_path.exists():
            console.print(f"  [green]✓[/green] {area}")
        else:
            console.print(f"  [red]✗[/red] {area} [dim]- NOT FOUND[/dim]")
            add_issue(
                f"Missing folder: {area}",
                fix_action=lambda p=area_path: p.mkdir(parents=True, exist_ok=True),
                fix_description=f"Create {area}"
            )

    # Check governance files
    console.print("\n[bold]Checking governance files...[/bold]")
    required_files = [
        '.editorconfig',
        '.gitignore',
        '00.00_index.md',
        '.devbase_state.json'
    ]

    for file in required_files:
        file_path = root / file
        if file_path.exists():
            console.print(f"  [green]✓[/green] {file}")
        else:
            console.print(f"  [yellow]⚠[/yellow] {file} [dim]- NOT FOUND[/dim]")
            # Some files can be auto-created
            if file == '.editorconfig':
                add_issue(
                    f"Missing: {file}",
                    fix_action=lambda p=file_path: p.write_text("root = true\n\n[*]\nindent_style = space\nindent_size = 4\n"),
                    fix_description="Create default .editorconfig"
                )

    # Check Air-Gap
    console.print("\n[bold]Checking Air-Gap protection...[/bold]")
    private_vault = root / "10-19_KNOWLEDGE" / "12_private_vault"
    gitignore = root / ".gitignore"

    if private_vault.exists():
        if gitignore.exists():
            content = gitignore.read_text()
            if "12_private_vault" in content:
                console.print("  [green]✓[/green] Private Vault is protected")
            else:
                console.print("  [red]✗[/red] Private Vault NOT in .gitignore!")
                add_issue(
                    "Private Vault exposed to Git",
                    fix_action=lambda: gitignore.write_text(content + "\n# Private vault (security)\n12_private_vault/\n"),
                    fix_description="Add 12_private_vault to .gitignore"
                )
        else:
            console.print("  [yellow]⚠[/yellow] No .gitignore found")

    # Check state file
    console.print("\n[bold]Checking state file...[/bold]")
    state_path = root / ".devbase_state.json"
    if state_path.exists():
        try:
            state_mgr = StateManager(root)
            state = state_mgr.get_state()
            console.print(f"  [green]✓[/green] Version: {state['version']}")
            console.print(f"  [dim]  Installed: {state.get('installedAt', 'Unknown')}[/dim]")
        except Exception as e:
            console.print(f"  [red]✗[/red] State file corrupted")
            add_issue(
                "Corrupted state file",
                fix_action=lambda: state_path.unlink() if state_path.exists() else None,
                fix_description="Reset state file (will be recreated on next setup)"
            )
    else:
        console.print("  [yellow]⚠[/yellow] State file not found")

    # Run security checks
    from devbase.commands.security_check import run_security_checks
    security_ok = run_security_checks(root)
    if not security_ok:
        add_issue("Security issues detected", fix_description="Review security audit above")

    # === FIX-IT FLOW ===
    console.print()
    console.print("=" * 50)
    
    if not issues:
        console.print("[bold green]✓ DevBase is HEALTHY[/bold green]")
        return
    
    # Report issues
    console.print(f"[bold yellow]Found {len(issues)} issue(s)[/bold yellow]\n")
    
    fixable = [i for i in issues if i["fix_action"]]
    
    if not fixable:
        console.print("[dim]No auto-fixes available. Please fix manually.[/dim]")
        return
    
    # Interactive fix flow
    if fix:
        # Auto-fix mode
        console.print("[bold]Auto-fixing issues...[/bold]\n")
        for issue in fixable:
            try:
                issue["fix_action"]()
                console.print(f"  [green]✓[/green] {issue['fix_description']}")
            except Exception as e:
                console.print(f"  [red]✗[/red] Failed: {issue['fix_description']} ({e})")
        console.print("\n[green]Done! Run [cyan]devbase doctor[/cyan] again to verify.[/green]")
    else:
        # Interactive mode
        console.print(f"[bold]{len(fixable)} issue(s) can be auto-fixed:[/bold]\n")
        for i, issue in enumerate(fixable, 1):
            console.print(f"  {i}. {issue['description']}")
            console.print(f"     [dim]→ {issue['fix_description']}[/dim]")
        
        console.print()
        if Confirm.ask("[bold]Fix all issues now?[/bold]"):
            for issue in fixable:
                try:
                    issue["fix_action"]()
                    console.print(f"  [green]✓[/green] {issue['fix_description']}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed: {e}")
            console.print("\n[green]Done![/green]")
        else:
            console.print("\n[dim]Run [cyan]devbase doctor --fix[/cyan] to auto-fix later.[/dim]")




@app.command()
def hydrate(
    ctx: typer.Context,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing templates"),
    ] = False,
) -> None:
    """
    💧 Update workspace templates and configurations.
    
    Syncs the latest templates from the DevBase repository
    without affecting your projects or data.
    """
    root: Path = ctx.obj["root"]

    console.print()
    console.print("[bold]Hydrating workspace...[/bold]")

    if force:
        console.print("[yellow]⚠️  Force mode: All templates will be overwritten[/yellow]\n")

    # Execute hydration (reusing setup modules)
    fs = FileSystem(str(root), dry_run=False)

    modules_to_run = [
        ("Core", run_setup_core),
        ("PKM", run_setup_pkm),
        ("Code", run_setup_code),
        ("Operations", run_setup_operations),
    ]

    class LegacyUI:
        def print_header(self, msg): pass
        def print_step(self, msg, status): pass

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for name, run_func in modules_to_run:
            task = progress.add_task(f"Hydrating {name}...", total=None)
            try:
                run_func(fs, LegacyUI(), policy_version=POLICY_VERSION)
                progress.update(task, description=f"[green]✓[/green] {name}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] {name}")
                console.print(f"[red]Error: {e}[/red]")

    console.print("\n[bold green]✓ Hydration complete![/bold green]")


@app.command(name="hydrate-icons")
def hydrate_icons_cmd(ctx: typer.Context) -> None:
    """
    🎨 Apply custom icons to Johnny.Decimal folders.
    
    Uses Neo-Glassmorphism style icons from ./devbase/icons/
    to make folder navigation more intuitive.
    
    Requirements:
    - Place icon files (00.ico, 10.ico, etc.) in ~/.devbase/icons/
    - Windows: .ico format
    - macOS: .icns or .png format
    - Linux: .png format
    
    Example:
        devbase core hydrate-icons
    """
    root: Path = ctx.obj["root"]
    
    console.print()
    console.print("[bold]Applying folder icons...[/bold]\n")
    
    from devbase.utils.icons import hydrate_icons, get_icon_dir
    
    icon_dir = get_icon_dir()
    if not icon_dir.exists():
        console.print(f"[yellow]Icon directory not found:[/yellow] [dim]{icon_dir}[/dim]")
        console.print("\n[bold]To set up icons:[/bold]")
        console.print("  1. Create directory: [cyan]mkdir ~/.devbase/icons[/cyan]")
        console.print("  2. Add icon files: 00.ico, 10.ico, 20.ico, 30.ico, 40.ico, 90.ico")
        console.print("  3. Run this command again")
        console.print("\n[dim]Generate icons using the prompts in Style Guide.[/dim]")
        return
    
    results = hydrate_icons(root)
    
    applied = sum(1 for v in results.values() if v)
    console.print()
    console.print(f"[bold green]✓ Applied {applied}/{len(results)} icons[/bold green]")

