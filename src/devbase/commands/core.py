"""
Core Commands: setup, doctor, hydrate
======================================
Essential workspace management commands.
"""
from datetime import datetime
from pathlib import Path
import importlib.metadata
import shutil

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Confirm
from typing_extensions import Annotated

from devbase.commands.debug import debug_cmd
from devbase.utils.filesystem import get_filesystem
from devbase.utils.state import get_state_manager

app = typer.Typer(help="Core workspace commands")
console = Console()

app.command(name="debug")(debug_cmd)

try:
    SCRIPT_VERSION = importlib.metadata.version("devbase")
except importlib.metadata.PackageNotFoundError:
    SCRIPT_VERSION = "5.1.0-alpha.3"

POLICY_VERSION = "5.0"

# Data-driven folder structure
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
        "30-39_OPERATIONS/31_backups",
        "30-39_OPERATIONS/32_automation",
    ],
    "Media Assets": [
        "40-49_MEDIA_ASSETS/40_images",
        "40-49_MEDIA_ASSETS/41_videos",
        "40-49_MEDIA_ASSETS/42_audio",
        "40-49_MEDIA_ASSETS/43_fonts",
        "40-49_MEDIA_ASSETS/44_design_sources",
    ],
}


def run_setup_module(fs, module_name: str, policy_version=None) -> None:
    """Create folders for a module from FOLDER_STRUCTURE."""
    folders = FOLDER_STRUCTURE.get(module_name, [])
    for folder in folders:
        fs.ensure_dir(folder)


def create_governance_files(fs) -> None:
    """Create default governance files if they don't exist."""
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

    if not fs.exists(".gitignore"):
        fs.write_atomic(".gitignore",
            "# DevBase Global Workspace Ignore\n"
            ".devbase_state.json\n"
            ".telemetry/\n"
            "__pycache__/\n"
            "*.pyc\n"
            ".DS_Store\n\n"
            "# Areas with independent lifecycles (Managed as separate repos or too large)\n"
            "20-29_CODE/\n"
            "30-39_OPERATIONS/31_backups/\n"
            "40-49_MEDIA_ASSETS/\n"
            "90-99_ARCHIVE_COLD/\n\n"
            "# Security (Air-Gap Protection)\n"
            "10-19_KNOWLEDGE/12_private_vault/\n"
            "*.env\n"
        )

    if not fs.exists("00-09_SYSTEM/00.00_index.md"):
        fs.write_atomic("00-09_SYSTEM/00.00_index.md",
            "# Johnny.Decimal Index\n\n"
            "Master index of the workspace.\n"
        )


def run_setup_core(fs, policy_version=None):
    run_setup_module(fs, "Core Structure", policy_version)
    create_governance_files(fs)
    required_subfolders = [
        '00-09_SYSTEM/00_inbox', '00-09_SYSTEM/01_dotfiles',
        '00-09_SYSTEM/05_templates', '00-09_SYSTEM/07_documentation',
        '10-19_KNOWLEDGE/10_guides_and_references', '10-19_KNOWLEDGE/11_public_garden',
        '10-19_KNOWLEDGE/12_private_vault', '10-19_KNOWLEDGE/13_architecture_and_specs',
        '10-19_KNOWLEDGE/14_library', '20-29_CODE/21_monorepo_apps',
        '20-29_CODE/22_worktrees', '20-29_CODE/23_playground',
        '30-39_OPERATIONS/31_backups', '30-39_OPERATIONS/32_automation',
        '40-49_MEDIA_ASSETS/40_images', '40-49_MEDIA_ASSETS/41_videos',
        '40-49_MEDIA_ASSETS/42_audio', '40-49_MEDIA_ASSETS/43_fonts',
        '40-49_MEDIA_ASSETS/44_design_sources',
    ]
    for subfolder in required_subfolders:
        fs.ensure_dir(subfolder)
    copy_built_in_templates(fs, "core/00-09_SYSTEM", "00-09_SYSTEM")


def run_setup_pkm(fs, policy_version=None):
    run_setup_module(fs, "Knowledge Management", policy_version)


def copy_built_in_templates(fs, category: str, destination: str):
    import logging
    import devbase
    logger = logging.getLogger(__name__)
    pkg_root = Path(devbase.__file__).parent
    tmpl_src = pkg_root / "templates" / category
    if not tmpl_src.exists():
        return
    dest_path = Path(fs.root) / destination
    fs.ensure_dir(destination)
    if getattr(fs, 'dry_run', False):
        return
    for item in tmpl_src.iterdir():
        if item.name.startswith("__template-") or item.name.endswith(".template"):
            src, dst = item, dest_path / item.name
            try:
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            except OSError as e:
                logger.warning(f"Failed to copy template {item.name}: {e}")


def run_setup_code(fs, policy_version=None):
    run_setup_module(fs, "Code Templates", policy_version)
    copy_built_in_templates(fs, "code", "00-09_SYSTEM/05_templates")


def run_setup_ai(fs, policy_version=None):
    run_setup_module(fs, "AI Integration", policy_version)


def run_setup_operations(fs, policy_version=None):
    run_setup_module(fs, "Operations", policy_version)


def run_setup_media(fs, policy_version=None):
    run_setup_module(fs, "Media Assets", policy_version)


@app.command()
def setup(
    ctx: typer.Context,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing governance files and templates")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show planned changes without executing them")] = False,
    interactive: Annotated[bool, typer.Option("--interactive/--no-interactive", "-i", help="Launch the interactive wizard")] = True,
) -> None:
    """
    🚀 [bold]Initialize or update your DevBase environment.[/bold]

    This is the first command you should run. It creates the Johnny.Decimal 
    directory structure and deploys core governance files (.gitignore, .editorconfig).

    [bold]EXAMPLES:[/bold]
      $ devbase core setup              # Recommended (Interactive)
      $ devbase core setup --no-i       # Automated (Uses defaults)
      $ devbase core setup --force      # Repair broken structure
    """
    root: Path = ctx.obj["root"]
    state_file = root / ".devbase_state.json"
    if not state_file.exists() and interactive and not dry_run:
        from devbase.utils.wizard import execute_setup_with_config, run_interactive_wizard
        try:
            config = run_interactive_wizard(suggested_path=root)
            execute_setup_with_config(config)
            return
        except KeyboardInterrupt:
            console.print("\n[yellow]Setup cancelled.[/yellow]")
            raise typer.Exit(0)

    console.print(Panel.fit(f"[bold cyan]DevBase Setup v{SCRIPT_VERSION}[/bold cyan]\nWorkspace: [yellow]{root}[/yellow]", border_style="cyan"))
    fs, state_mgr = get_filesystem(str(root), dry_run=dry_run), get_state_manager(root)
    current_state = state_mgr.get_state()
    
    modules = [
        ("Core Architecture", run_setup_core), ("Knowledge Engine", run_setup_pkm),
        ("Project Scaffolding", run_setup_code), ("AI Infrastructure", run_setup_ai),
        ("Ops & Automation", run_setup_operations), ("Asset Management", run_setup_media),
    ]

    console.print("[bold]Building your EOS environment...[/bold]")
    with Progress(SpinnerColumn(spinner_name="dots"), TextColumn("[progress.description]{task.description}"), 
                  typer.rich_utils.rich.progress.BarColumn(bar_width=None), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                  console=console, transient=True) as progress:
        total_task = progress.add_task("[cyan]Initializing...", total=len(modules))
        for name, run_func in modules:
            progress.update(total_task, description=f"[bold white]Deploying {name}...[/bold white]")
            try:
                run_func(fs, policy_version=POLICY_VERSION)
                progress.advance(total_task)
            except Exception as e:
                console.print(f"[red]✗ Critical failure in {name}: {e}[/red]")
                raise typer.Exit(1)

    if not dry_run:
        new_state = current_state.copy()
        new_state.update({"version": SCRIPT_VERSION, "policyVersion": POLICY_VERSION, "lastUpdate": datetime.now().isoformat()})
        if not new_state.get("installedAt"): new_state["installedAt"] = new_state["lastUpdate"]
        state_mgr.save_state(new_state)
    
    console.print(Panel("[bold green]✅ Setup Complete![/bold green]", border_style="green"))


@app.command()
def doctor(
    ctx: typer.Context,
    fix: Annotated[bool, typer.Option("--fix", "-f", help="Automatically apply all recommended repairs")] = False,
) -> None:
    """
    🏥 [bold]Verify workspace health and repair system issues.[/bold]

    Checks for:
    1. [bold]Environment:[/bold] Conflicting global scripts (Ghosts).
    2. [bold]Structure:[/bold] Missing Johnny.Decimal directories.
    3. [bold]Governance:[/bold] Outdated or missing .gitignore/.editorconfig.
    4. [bold]Security:[/bold] Air-Gap exposure of private vaults.

    [bold]USAGE:[/bold]
      $ devbase core doctor         # Audit only
      $ devbase core doctor --fix   # Audit and repair everything
    """
    from devbase.commands.doctor.checks import StructureCheck, GovernanceCheck, SecurityCheck, EnvironmentCheck
    root: Path = ctx.obj["root"]
    console.print(f"\n[bold]DevBase Health Check[/bold]\n[dim]Workspace: {root}[/dim]\n")

    state_file = root / ".devbase_state.json"
    checks = [EnvironmentCheck(root)]
    if state_file.exists():
        checks.extend([StructureCheck(root), GovernanceCheck(root), SecurityCheck(root)])
    else:
        console.print("[yellow]ℹ No workspace detected. Skipping folder checks.[/yellow]\n")

    all_issues = []
    for check in checks:
        console.print(f"[bold]Running {check.__class__.__name__}...[/bold]")
        issues = check.run()
        if not issues: console.print("  [green]✓[/green] Passed")
        else:
            for issue in issues: console.print(f"  [red]✗[/red] {issue.description}")
            all_issues.extend(issues)

    console.print("\n" + "=" * 50)
    if not all_issues:
        console.print("[bold green]✓ DevBase is HEALTHY[/bold green]")
        return

    console.print(f"[bold yellow]Found {len(all_issues)} issue(s)[/bold yellow]\n")
    fixable = [i for i in all_issues if i.fix_action]
    if not fixable:
        console.print("[dim]No auto-fixes available.[/dim]")
        return

    if not fix:
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column("Issue Detected", style="bold red")
        table.add_column("Proposed Fix", style="green")
        for i, issue in enumerate(fixable, 1):
            table.add_row(str(i), issue.description, issue.fix_description)
        console.print(table)
        if not Confirm.ask("\n[bold]Do you want to apply these fixes now?[/bold]"): return

    console.print(f"\n[bold]{'Auto-fixing' if fix else 'Applying'} issues...[/bold]\n")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        task = progress.add_task("Fixing...", total=len(fixable))
        for issue in fixable:
            try:
                issue.fix_action()
                progress.console.print(f"  [green]✓[/green] {issue.fix_description}")
            except Exception as e:
                progress.console.print(f"  [red]✗[/red] Failed: {issue.fix_description} ({e})")
            progress.advance(task)
    console.print("\n[green]Done![/green]")


@app.command()
def hydrate(
    ctx: typer.Context,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite templates")] = False,
) -> None:
    root: Path = ctx.obj["root"]
    console.print("\n[bold]Hydrating workspace...[/bold]")
    fs = get_filesystem(str(root), dry_run=False)
    modules = [("Core", run_setup_core), ("PKM", run_setup_pkm), ("Code", run_setup_code), ("Operations", run_setup_operations)]
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        for name, run_func in modules:
            task = progress.add_task(f"Hydrating {name}...", total=None)
            try:
                run_func(fs, policy_version=POLICY_VERSION)
                progress.update(task, description=f"[green]✓[/green] {name}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] {name}")
    console.print("\n[bold green]✓ Hydration complete![/bold green]")


@app.command(name="hydrate-icons")
def hydrate_icons_cmd(ctx: typer.Context) -> None:
    root: Path = ctx.obj["root"]
    console.print("\n[bold]Applying folder icons...[/bold]\n")
    from devbase.utils.icons import get_icon_dir, hydrate_icons
    icon_dir = get_icon_dir()
    if not icon_dir.exists():
        console.print(f"[yellow]Icon directory not found: {icon_dir}[/yellow]")
        return
    results = hydrate_icons(root)
    console.print(f"\n[bold green]✓ Applied {sum(1 for v in results.values() if v)}/{len(results)} icons[/bold green]")
