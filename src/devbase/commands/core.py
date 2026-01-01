"""
Core Commands: setup, doctor, hydrate
======================================
Essential workspace management commands.
"""
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typing_extensions import Annotated

from devbase.commands.debug import debug_cmd
from devbase.utils.filesystem import get_filesystem
from devbase.utils.state import get_state_manager

app = typer.Typer(help="Core workspace commands")
console = Console()

app.command(name="debug")(debug_cmd)

import importlib.metadata

try:
    SCRIPT_VERSION = importlib.metadata.version("devbase")
except importlib.metadata.PackageNotFoundError:
    SCRIPT_VERSION = "5.1.0-alpha.3"

POLICY_VERSION = "5.0"

# Data-driven folder structure (replaces 5 stub functions)
FOLDER_STRUCTURE = {
    "Core Structure": [
        "00-09_SYSTEM",
        "10-19_KNOWLEDGE",
        "20-29_CODE",
        "30-39_OPERATIONS",
        "40-49_MEDIA_ASSETS",
        "90-99_ARCHIVE_COLD",
    ],
    "Knowledge Management": [
        "10-19_KNOWLEDGE/11_public_garden",
        "10-19_KNOWLEDGE/12_private_vault",
    ],
    "Code Templates": [
        "20-29_CODE/21_monorepo_apps",
        "20-29_CODE/22_worktrees",
        "20-29_CODE/23_playground",
    ],
    "AI Integration": [
        "00-09_SYSTEM/05_templates",
    ],
    "Operations": [
        "30-39_OPERATIONS/31_backup",
        "30-39_OPERATIONS/32_automation",
    ],
}


def run_setup_module(fs, module_name: str, policy_version=None) -> None:
    """Create folders for a module from FOLDER_STRUCTURE."""
    folders = FOLDER_STRUCTURE.get(module_name, [])
    for folder in folders:
        fs.ensure_dir(folder)



def create_governance_files(fs) -> None:
    """Create default governance files if they don't exist."""
    # .editorconfig
    if not fs.exists(".editorconfig"):
        fs.write_atomic(".editorconfig",
            "root = true\n\n"
            "[*]\n"
            "indent_style = space\n"
            "indent_size = 4\n"
            "charset = utf-8\n"
            "trim_trailing_whitespace = true\n"
            "insert_final_newline = true\n"
        )

    # .gitignore
    if not fs.exists(".gitignore"):
        fs.write_atomic(".gitignore",
            "# DevBase\n"
            ".devbase_state.json\n"
            "__pycache__/\n"
            "*.pyc\n"
            ".DS_Store\n\n"
            "# Security\n"
            "12_private_vault/\n"
            "*.env\n"
        )

    # 00.00_index.md
    if not fs.exists("00-09_SYSTEM/00.00_index.md"):
        fs.write_atomic("00-09_SYSTEM/00.00_index.md",
            "# Johnny.Decimal Index\n\n"
            "Master index of the workspace.\n"
        )


# Legacy API compatibility wrappers (for wizard.py imports)
def run_setup_core(fs, policy_version=None):
    run_setup_module(fs, "Core Structure", policy_version)
    create_governance_files(fs)

    # Create required subfolders
    required_subfolders = [
        '00-09_SYSTEM/00_inbox',
        '00-09_SYSTEM/01_dotfiles',
        '00-09_SYSTEM/07_documentation',
        '10-19_KNOWLEDGE/10_references',
        '10-19_KNOWLEDGE/11_public_garden',
        '10-19_KNOWLEDGE/12_private_vault',
        '20-29_CODE/21_monorepo_apps',
        '20-29_CODE/22_worktrees',
        '20-29_CODE/23_playground',
        '30-39_OPERATIONS/31_backups',
        '30-39_OPERATIONS/32_automation',
    ]

    for subfolder in required_subfolders:
        fs.ensure_dir(subfolder)

    # Deploy subfolder templates from core templates
    copy_built_in_templates(fs, "core/00-09_SYSTEM", "00-09_SYSTEM")


def run_setup_pkm(fs, policy_version=None):
    run_setup_module(fs, "Knowledge Management", policy_version)


import shutil


def copy_built_in_templates(fs, category: str, destination: str):
    """Copy built-in templates from package to workspace."""
    import devbase
    pkg_root = Path(devbase.__file__).parent
    tmpl_src = pkg_root / "templates" / category

    if not tmpl_src.exists():
        return

    dest_path = Path(fs.root) / destination

    for item in tmpl_src.iterdir():
        if item.name.startswith("__template-") or item.name.endswith(".template"):
            src = item
            dst = dest_path / item.name

            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

def run_setup_code(fs, policy_version=None):
    run_setup_module(fs, "Code Templates", policy_version)
    copy_built_in_templates(fs, "code", "20-29_CODE")



def run_setup_ai(fs, policy_version=None):
    run_setup_module(fs, "AI Integration", policy_version)


def run_setup_operations(fs, policy_version=None):
    run_setup_module(fs, "Operations", policy_version)


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
        typer.Option("--interactive/--no-interactive", "-i", help="Run interactive setup wizard"),
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

    # Initialize filesystem via adapter
    fs = get_filesystem(str(root), dry_run=dry_run)
    state_mgr = get_state_manager(root)

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
                run_func(fs, policy_version=POLICY_VERSION)
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
    # Success message
    msg = f"""
[bold green]✅ Setup Complete![/bold green]

DevBase v{SCRIPT_VERSION} is ready.

Next steps:
  1. [cyan]devbase core doctor[/cyan] - Verify installation
  2. [cyan]devbase dev new my-project[/cyan] - Create first project
    """
    console.print(Panel(msg.strip(), border_style="green"))


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

    # Check required subfolders (Johnny.Decimal categories)
    console.print("\n[bold]Checking required subfolders...[/bold]")
    required_subfolders = [
        '00-09_SYSTEM/00_inbox',
        '00-09_SYSTEM/01_dotfiles',
        '00-09_SYSTEM/07_documentation',
        '10-19_KNOWLEDGE/10_references',
        '10-19_KNOWLEDGE/11_public_garden',
        '10-19_KNOWLEDGE/12_private_vault',
        '20-29_CODE/21_monorepo_apps',
        '20-29_CODE/22_worktrees',
        '20-29_CODE/23_playground',
        '30-39_OPERATIONS/31_backups',
        '30-39_OPERATIONS/32_automation',
    ]

    for subfolder in required_subfolders:
        folder_path = root / subfolder
        if folder_path.exists():
            console.print(f"  [green]✓[/green] {subfolder}")
        else:
            console.print(f"  [red]✗[/red] {subfolder} [dim]- NOT FOUND[/dim]")
            add_issue(
                f"Missing subfolder: {subfolder}",
                fix_action=lambda p=folder_path: p.mkdir(parents=True, exist_ok=True),
                fix_description=f"Create {subfolder}"
            )

    # Check governance files
    console.print("\n[bold]Checking governance files...[/bold]")
    required_files = [
        '.editorconfig',
        '.gitignore',
        '00-09_SYSTEM/00.00_index.md',
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
            state_mgr = get_state_manager(root)
            state = state_mgr.get_state()
            console.print(f"  [green]✓[/green] Version: {state['version']}")
            console.print(f"  [dim]  Installed: {state.get('installedAt', 'Unknown')}[/dim]")
        except Exception:
            console.print("  [red]✗[/red] State file corrupted")
            add_issue(
                "Corrupted state file",
                fix_action=lambda: state_path.unlink() if state_path.exists() else None,
                fix_description="Reset state file (will be recreated on next setup)"
            )
    else:
        console.print("  [yellow]⚠[/yellow] State file not found")

    # Check Templates
    console.print("\n[bold]Checking templates...[/bold]")
    templates_dir = root / "20-29_CODE"
    clean_arch = templates_dir / "__template-clean-arch"

    if clean_arch.exists():
        console.print("  [green]✓[/green] Code templates installed")
    else:
        console.print("  [red]✗[/red] Templates missing in 20-29_CODE")
        add_issue(
            "Missing default code templates",
            fix_action=lambda: run_setup_code(get_filesystem(str(root), dry_run=False)),
            fix_description="Hydrate code templates"
        )

    # Run security checks
    from devbase.commands.security_check import run_security_checks
    security_ok = run_security_checks(root)
    if not security_ok:
        add_issue("Security issues detected", fix_description="Review security audit above")

    # Check Projects (New Governance Check)
    console.print("\n[bold]Checking Projects health (Governance)...[/bold]")
    apps_dir = root / "20-29_CODE" / "21_monorepo_apps"
    if apps_dir.exists():
        projects = [p for p in apps_dir.iterdir() if p.is_dir()]
        console.print(f"  Found {len(projects)} projects.")

        for proj in projects:
            issues_found = False
            # Check Git
            if not (proj / ".git").exists():
                console.print(f"  [red]✗[/red] {proj.name}: Missing .git")
                issues_found = True
                add_issue(f"Project {proj.name} not initialized", fix_description="Run 'git init' manually")

            # Check Pre-commit (soft check)
            if not (proj / ".pre-commit-config.yaml").exists():
                # Not necessarily an error, but a warning for governance
                # console.print(f"  [yellow]⚠[/yellow] {proj.name}: No pre-commit config")
                pass

            if not issues_found:
                 console.print(f"  [green]✓[/green] {proj.name}")

    # Check Worktrees for stale branches
    console.print("\n[bold]Checking Worktrees health...[/bold]")
    worktrees_dir = root / "20-29_CODE" / "22_worktrees"
    if worktrees_dir.exists():
        worktrees = [w for w in worktrees_dir.iterdir() if w.is_dir()]
        if worktrees:
            console.print(f"  Found {len(worktrees)} worktrees.")

            for wt in worktrees:
                # Check if worktree has uncommitted changes
                import subprocess
                try:
                    result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=str(wt),
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.stdout.strip():
                        console.print(f"  [yellow]⚠[/yellow] {wt.name}: Uncommitted changes")
                    else:
                        console.print(f"  [green]✓[/green] {wt.name}")
                except:
                    console.print(f"  [dim]?[/dim] {wt.name}: Could not check status")
        else:
            console.print("  [dim]No worktrees found.[/dim]")
    else:
        console.print("  [dim]No worktrees directory.[/dim]")

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

        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column("Issue Detected", style="bold red")
        table.add_column("Proposed Fix", style="green")

        for i, issue in enumerate(fixable, 1):
            table.add_row(str(i), issue['description'], issue['fix_description'])

        console.print(table)
        console.print()

        if Confirm.ask("[bold]Do you want to apply these fixes now?[/bold]"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Applying fixes...", total=len(fixable))

                for issue in fixable:
                    try:
                        issue["fix_action"]()
                        progress.console.print(f"  [green]✓[/green] {issue['fix_description']}")
                    except Exception as e:
                        progress.console.print(f"  [red]✗[/red] Failed: {e}")
                    progress.advance(task)

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

    # Execute hydration via adapters
    fs = get_filesystem(str(root), dry_run=False)

    modules_to_run = [
        ("Core", run_setup_core),
        ("PKM", run_setup_pkm),
        ("Code", run_setup_code),
        ("Operations", run_setup_operations),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for name, run_func in modules_to_run:
            task = progress.add_task(f"Hydrating {name}...", total=None)
            try:
                run_func(fs, policy_version=POLICY_VERSION)
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

    from devbase.utils.icons import get_icon_dir, hydrate_icons

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

