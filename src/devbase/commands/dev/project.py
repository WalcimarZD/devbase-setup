"""
Project Management Commands
=============================
Commands for creating, importing, listing, and managing projects.
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

app = typer.Typer()
console = Console()
logger = logging.getLogger(__name__)


def _get_ghostwriter(root: Path):
    """Lazy import for ADR ghostwriter."""
    from devbase.services.adr_generator import get_ghostwriter
    return get_ghostwriter(root)


@app.command()
def new(
    ctx: typer.Context,
    name: Annotated[Optional[str], typer.Argument(help="Project name (kebab-case)")] = None,
    template: Annotated[
        str,
        typer.Option("--template", "-t", help="Template name"),
    ] = "clean-arch",
    interactive: Annotated[
        bool,
        typer.Option("--interactive/--no-interactive", help="Customize project details"),
    ] = True,
    setup: Annotated[
        bool,
        typer.Option("--setup/--no-setup", help="Run full project setup (git, deps, VS Code)"),
    ] = True,
) -> None:
    """
    📦 Create a new project from template.

    Creates a customized project in 21_monorepo_apps/ using the specified template.

    Golden Path (Default):
    - Generates files
    - Initializes Git repo
    - Installs dependencies (uv/pip)
    - Sets up pre-commit hooks
    - Opens in VS Code

    Use --no-setup to only generate files.
    """
    root: Path = ctx.obj["root"]

    if name is None:
        from rich.prompt import Prompt
        name = Prompt.ask("Project name (kebab-case)")

    if not re.match(r'^[a-z0-9]+([-.][a-z0-9]+)*$', name):
        from rich.prompt import Confirm

        console.print(f"[red]✗ Project name '{name}' is not kebab-case.[/red]")

        suggestion = re.sub(r'([a-z])([A-Z])', r'\1-\2', name).lower()
        suggestion = re.sub(r'[_ ]', '-', suggestion)
        suggestion = re.sub(r'[^a-z0-9-]', '', suggestion)

        if suggestion and suggestion != name:
            if Confirm.ask(f"Did you mean [bold cyan]{suggestion}[/bold cyan]?", default=True):
                name = suggestion
                console.print(f"[green]✓ Using '{name}'[/green]\n")
            else:
                raise typer.Exit(1)
        else:
            console.print("  [dim]Name must contain only lowercase letters, numbers, and hyphens.[/dim]")
            raise typer.Exit(1)

    from devbase.utils.templates import generate_project_from_template, list_available_templates
    from devbase.services.project_setup import get_project_setup
    from devbase.utils.telemetry import get_telemetry

    telemetry = get_telemetry(root)
    setup_service = get_project_setup(root)

    telemetry.track(
        f"Creating project {name}",
        category="scaffolding",
        action="create_project_start",
        metadata={"template": template, "interactive": interactive}
    )

    try:
        console.print()
        console.print(f"[bold]Creating project '{name}'...[/bold]\n")

        dest_path = generate_project_from_template(
            template_name=template,
            project_name=name,
            root=root,
            interactive=interactive
        )
        console.print(f"[green]✓[/green] Files generated at {dest_path}")

        if setup:
            setup_service.run_golden_path(dest_path, name, interactive=interactive)
        else:
            console.print("\n[dim]Skipping setup steps (--no-setup)[/dim]")
            console.print(f"\nNext steps:\n  cd {dest_path}\n  git init\n  code .")

        console.print(Panel.fit(
            f"[bold green]✅ Project Ready![/bold green]\n\n"
            f"Location: [cyan]{dest_path}[/cyan]",
            border_style="green"
        ))

        telemetry.track(
            f"Created project {name}",
            category="scaffolding",
            action="create_project_success",
            metadata={"path": str(dest_path), "setup_run": setup}
        )

    except FileNotFoundError:
        telemetry.track(f"Template not found: {template}", action="create_project_error", status="error")
        console.print(f"[red]✗ Template '{template}' not found[/red]\n")
        console.print("Available templates:")
        for tmpl in list_available_templates(root):
            console.print(f"  [cyan]• {tmpl}[/cyan]")
        raise typer.Exit(1)
    except FileExistsError:
        telemetry.track(f"Project exists: {name}", action="create_project_error", status="error")
        console.print(f"[red]✗ Project '{name}' already exists[/red]")
        raise typer.Exit(1)
    except Exception as e:
        telemetry.track(f"Create failed: {e}", action="create_project_error", status="error")
        console.print(f"[red]✗ Failed to create project: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="import")
def import_project(
    ctx: typer.Context,
    source: Annotated[str, typer.Argument(help="Git URL or local path to import")],
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Override project name")
    ] = None,
    restore: Annotated[
        bool,
        typer.Option("--restore", "-r", help="Run NuGet restore after import (.NET projects)")
    ] = False,
) -> None:
    """
    📥 Import an existing project (brownfield).

    Clones a Git repository or copies a local project into the DevBase workspace.
    Imported projects are marked as 'external' and exempt from governance rules.

    Examples:
        devbase dev import https://github.com/user/repo.git
        devbase dev import https://github.com/user/dotnet-app.git --restore
        devbase dev import D:\\Projects\\legacy-app --name legacy
    """
    import subprocess
    import shutil
    import devbase

    root: Path = ctx.obj["root"]
    apps_dir = root / "20-29_CODE" / "21_monorepo_apps"
    apps_dir.mkdir(parents=True, exist_ok=True)

    is_url = source.startswith("http://") or source.startswith("https://") or source.startswith("git@")

    if is_url:
        repo_name = name or source.rstrip("/").split("/")[-1].replace(".git", "")
        dest_path = apps_dir / repo_name

        if dest_path.exists():
            console.print(f"[red]✗ Project '{repo_name}' already exists.[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold]Importing project from Git...[/bold]")
        console.print(f"[dim]Source: {source}[/dim]")
        console.print(f"[dim]Destination: {dest_path}[/dim]\n")

        try:
            result = subprocess.run(
                ["git", "clone", "--", source, str(dest_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                console.print(f"[red]✗ Git clone failed:[/red]\n{result.stderr}")
                raise typer.Exit(1)
            console.print(f"[green]✓[/green] Repository cloned successfully")
        except FileNotFoundError:
            console.print("[red]✗ Git not found. Please install Git.[/red]")
            raise typer.Exit(1)
        except subprocess.TimeoutExpired:
            console.print("[red]✗ Clone timed out (120s).[/red]")
            raise typer.Exit(1)
    else:
        source_path = Path(source).resolve()
        if not source_path.exists():
            console.print(f"[red]✗ Source path not found: {source}[/red]")
            raise typer.Exit(1)

        project_name = name or source_path.name
        dest_path = apps_dir / project_name

        if dest_path.exists():
            console.print(f"[red]✗ Project '{project_name}' already exists.[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold]Importing local project...[/bold]")
        console.print(f"[dim]Source: {source_path}[/dim]")
        console.print(f"[dim]Destination: {dest_path}[/dim]\n")

        try:
            shutil.copytree(source_path, dest_path)
            console.print(f"[green]✓[/green] Project copied successfully")
        except OSError as e:
            console.print(f"[red]✗ Copy failed: {e}[/red]")
            raise typer.Exit(1)

    metadata = {
        "template": "imported",
        "governance": "external",
        "source": source,
        "imported_at": datetime.now().isoformat(),
        "devbase_version": devbase.__version__
    }

    meta_file = dest_path / ".devbase.json"
    meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] Created .devbase.json (governance: external)")

    console.print(Panel(
        f"[bold green]✅ Import Complete![/bold green]\n\n"
        f"Project: [cyan]{dest_path.name}[/cyan]\n"
        f"Location: [dim]{dest_path}[/dim]\n\n"
        f"[dim]This project is marked as 'external' and exempt from governance rules.[/dim]",
        border_style="green"
    ))

    if restore:
        from devbase.utils.nuget import nuget_restore, is_dotnet_project
        if is_dotnet_project(dest_path):
            console.print()
            nuget_restore(dest_path, root=root)
        else:
            console.print("[dim]--restore specified but no .NET project detected. Skipping.[/dim]")

    try:
        from devbase.utils.vscode import generate_vscode_workspace
        generate_vscode_workspace(dest_path, dest_path.name)
    except OSError as e:
        console.print(f"[yellow]⚠ Failed to generate workspace: {e}[/yellow]")


@app.command(name="open")
def open_project(
    ctx: typer.Context,
    project_name: Annotated[str | None, typer.Argument(help="Project name to open in VS Code")] = None,
) -> None:
    """
    💻 Open a project in VS Code.

    Opens the project's .code-workspace file or folder in VS Code.
    If no name is provided, an interactive list is shown.

    Examples:
        devbase dev open MedSempreMVC_GIT
        devbase dev open
    """
    from devbase.utils.vscode import open_in_vscode
    from rich.prompt import Prompt

    root: Path = ctx.obj["root"]
    project_path = None

    if not project_name:
        apps_dir = root / "20-29_CODE" / "21_monorepo_apps"
        worktrees_dir = root / "20-29_CODE" / "22_worktrees"

        candidates = []

        if apps_dir.exists():
            candidates.extend([p for p in apps_dir.iterdir() if p.is_dir()])

        if worktrees_dir.exists():
            candidates.extend([w for w in worktrees_dir.iterdir() if w.is_dir()])

        if not candidates:
            console.print("[yellow]No projects found to open.[/yellow]")
            console.print("Create one with: [cyan]devbase dev new[/cyan]")
            raise typer.Exit(1)

        candidates.sort(key=lambda x: x.name)

        console.print("\n[bold]Select a project to open:[/bold]")
        for i, path in enumerate(candidates, 1):
            kind = "Worktree" if path.parent.name == "22_worktrees" else "Project"
            color = "magenta" if kind == "Worktree" else "green"
            console.print(f"  [bold cyan]{i}.[/bold cyan] {path.name} [{color}]({kind})[/{color}]")

        console.print()
        choice = Prompt.ask("Enter number or name", default="1")

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                project_path = candidates[idx]
            else:
                console.print(f"[red]Invalid selection: {choice}[/red]")
                raise typer.Exit(1)
        else:
            project_name = choice

    if not project_path:
        project_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name

        if not project_path.exists():
            project_path = root / "20-29_CODE" / "22_worktrees" / project_name

    if not project_path.exists():
        console.print(f"[red]✗ Project '{project_name}' not found.[/red]")
        raise typer.Exit(1)

    open_in_vscode(project_path)


@app.command(name="restore-packages")
def restore_packages(
    ctx: typer.Context,
    project_name: Annotated[str, typer.Argument(help="Project name to restore packages for")],
    solution: Annotated[
        str,
        typer.Option("--solution", "-s", help="Specific .sln file to restore")
    ] = None,
) -> None:
    """
    📦 Restore NuGet packages for a .NET project.
    """
    from devbase.utils.nuget import nuget_restore, is_dotnet_project

    root: Path = ctx.obj["root"]
    project_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name

    if not project_path.exists():
        project_path = root / "20-29_CODE" / "22_worktrees" / project_name

    if not project_path.exists():
        console.print(f"[red]✗ Project '{project_name}' not found.[/red]")
        raise typer.Exit(1)

    if not is_dotnet_project(project_path):
        console.print(f"[yellow]⚠ '{project_name}' does not appear to be a .NET project.[/yellow]")
        raise typer.Exit(1)

    success = nuget_restore(project_path, solution, root=root)
    if not success:
        raise typer.Exit(1)


@app.command(name="restore")
def restore_project(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Project name to restore from archive")],
) -> None:
    """
    🔄 Restore an archived project.

    Moves the project from 90-99_ARCHIVE_COLD back to 21_monorepo_apps.
    Scans all years in the archive folder to find the project.
    """
    import shutil
    from devbase.utils.telemetry import get_telemetry

    root: Path = ctx.obj["root"]
    telemetry = get_telemetry(root)
    
    archive_root = root / "90-99_ARCHIVE_COLD" / "92_archived_projects"
    dest_dir = root / "20-29_CODE" / "21_monorepo_apps"
    
    # Find project in archive
    found_path = None
    if archive_root.exists():
        for year_dir in archive_root.iterdir():
            if year_dir.is_dir():
                target = year_dir / name
                if target.exists():
                    found_path = target
                    break
    
    if not found_path:
        console.print(f"[red]✗ Project '{name}' not found in archives.[/red]")
        raise typer.Exit(1)

    dest_path = dest_dir / name
    if dest_path.exists():
        console.print(f"[red]✗ Project '{name}' already exists in active projects.[/red]")
        raise typer.Exit(1)

    try:
        console.print(f"\n[bold blue]Restoring project...[/bold blue]")
        console.print(f"[dim]Source: {found_path}[/dim]")
        
        shutil.move(str(found_path), str(dest_path))
        
        console.print(f"[green]✓[/green] Project restored to: [bold]{dest_path}[/bold]")
        telemetry.track(f"Restored project {name}", category="lifecycle", action="restore_project")
    except Exception as e:
        console.print(f"[red]✗ Restore failed: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="info")
def info_project(
    ctx: typer.Context,
    project_name: Annotated[str, typer.Argument(help="Project name to inspect")]
) -> None:
    """
    ℹ️ Show project details.

    Displays template used, creation date, and metadata.
    """

    root: Path = ctx.obj["root"]
    project_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name

    if not project_path.exists():
        project_path = root / "20-29_CODE" / "22_worktrees" / project_name

    if not project_path.exists():
        console.print(f"[red]✗ Project '{project_name}' not found.[/red]")
        raise typer.Exit(1)

    meta_file = project_path / ".devbase.json"
    metadata = {}

    if meta_file.exists():
        try:
            metadata = json.loads(meta_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to parse .devbase.json for {project_name}: {e}")

    copier_file = project_path / ".copier-answers.yml"
    if not metadata and copier_file.exists():
        metadata["template"] = "copier-template (inferred)"

    stat = project_path.stat()
    created_ts = stat.st_ctime
    modified_ts = stat.st_mtime

    template = metadata.get("template", "Unknown / Custom")
    governance = metadata.get("governance", "full")
    created = metadata.get("created_at", metadata.get("imported_at", datetime.fromtimestamp(created_ts).strftime("%Y-%m-%d %H:%M")))
    version = metadata.get("devbase_version", "Pre-5.1.0")
    author = metadata.get("author", "Unknown")
    desc = metadata.get("description", "No description")
    source = metadata.get("source", None)

    if governance == "external":
        gov_display = "[yellow]External[/yellow] (Governance skipped)"
    elif governance == "partial":
        gov_display = "[blue]Partial[/blue]"
    else:
        gov_display = "[green]Full[/green]"

    grid = Table.grid(expand=True)
    grid.add_column(style="bold cyan", width=15)
    grid.add_column()

    grid.add_row("Project:", project_name)
    grid.add_row("Location:", str(project_path))
    grid.add_row("Governance:", gov_display)
    grid.add_row("Template:", template)
    if source:
        grid.add_row("Source:", source)
    grid.add_row("Created:", created)
    grid.add_row("DevBase Ver:", version)
    grid.add_row("Author:", author)
    grid.add_row("Description:", desc)

    console.print(Panel(grid, title=f"ℹ️ Project Info: {project_name}", border_style="blue"))


@app.command(name="list")
def list_projects(
    ctx: typer.Context,
    archived: Annotated[bool, typer.Option("--archived", "-a", help="List archived projects instead of active ones")] = False,
) -> None:
    """
    📂 List all projects.

    Scans workspace and displays a table of active or archived projects.
    """
    from devbase.utils.telemetry import get_telemetry

    root: Path = ctx.obj["root"]
    telemetry = get_telemetry(root)

    if archived:
        projects_dir = root / "90-99_ARCHIVE_COLD" / "92_archived_projects"
        title = "Archived Projects"
    else:
        projects_dir = root / "20-29_CODE" / "21_monorepo_apps"
        title = "Active Projects"

    console.print()
    console.print(f"[bold]{title}[/bold]")
    console.print(f"[dim]Location: {projects_dir}[/dim]\n")

    if not projects_dir.exists():
        console.print(f"[dim]No {title.lower()} found.[/dim]")
        return

    # Deep scan for archived projects (they are nested by year)
    if archived:
        projects = []
        for year_dir in projects_dir.iterdir():
            if year_dir.is_dir():
                projects.extend([p for p in year_dir.iterdir() if p.is_dir()])
    else:
        projects = [p for p in projects_dir.iterdir() if p.is_dir()]

    if not projects:
        console.print(f"[dim]No {title.lower()} found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Last Modified", justify="right")
    table.add_column("Governance", justify="center")

    for p in sorted(projects, key=lambda x: x.name):
        meta_file = p / ".devbase.json"
        governance = "full"
        template = None

        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                governance = meta.get("governance", "full")
                template = meta.get("template")
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(f"Could not read metadata for {p.name}: {e}")

        if template == "worktree":
            gov_badge = "[magenta]Worktree[/magenta]"
        elif governance == "external":
            gov_badge = "[yellow]External[/yellow]"
        elif governance == "partial":
            gov_badge = "[blue]Partial[/blue]"
        else:
            gov_badge = "[green]Full[/green]"

        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(p.name, mtime, gov_badge)

    # Add worktrees to active list
    if not archived:
        worktrees_dir = root / "20-29_CODE" / "22_worktrees"
        if worktrees_dir.exists():
            for wt in sorted(worktrees_dir.iterdir(), key=lambda x: x.name):
                if wt.is_dir():
                    mtime = datetime.fromtimestamp(wt.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    table.add_row(wt.name, mtime, "[magenta]Worktree[/magenta]")
                    projects.append(wt)

    console.print(table)
    console.print(f"\n[dim]Total: {len(projects)} projects[/dim]")

    telemetry.track(f"Listed {'archived' if archived else 'active'} projects", action="list_projects")


@app.command()
def archive(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Project name to archive")],
    confirm: Annotated[bool, typer.Option("--confirm", "-y", help="Skip confirmation")] = False,
) -> None:
    """
    📦 Archive a project.

    Moves the project from 21_monorepo_apps to 90-99_ARCHIVE_COLD/92_archived_projects/{year}.
    """
    import shutil
    from rich.prompt import Confirm
    from devbase.utils.telemetry import get_telemetry

    root: Path = ctx.obj["root"]
    telemetry = get_telemetry(root)

    project_path = root / "20-29_CODE" / "21_monorepo_apps" / name

    if not project_path.exists():
        console.print(f"[red]✗ Project '{name}' not found at {project_path}[/red]")
        raise typer.Exit(1)

    year = str(datetime.now().year)
    archive_root = root / "90-99_ARCHIVE_COLD" / "92_archived_projects" / year
    archive_path = archive_root / name

    console.print()
    console.print(Panel.fit(
        f"[bold red]Archive Project[/bold red]\n\n"
        f"Project: [cyan]{name}[/cyan]\n"
        f"Source: [dim]{project_path}[/dim]\n"
        f"Destination: [yellow]{archive_path}[/yellow]",
        border_style="red"
    ))

    if not confirm:
        if not Confirm.ask("Are you sure you want to archive this project?"):
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    try:
        archive_root.mkdir(parents=True, exist_ok=True)

        with console.status("[bold yellow]Archiving project...[/bold yellow]"):
            shutil.move(str(project_path), str(archive_path))

        console.print(f"\n[green]✓[/green] Project archived to: {archive_path}")

        telemetry.track(
            f"Archived project {name}",
            category="lifecycle",
            action="archive_project",
            metadata={"src": str(project_path), "dst": str(archive_path)}
        )

    except OSError as e:
        console.print(f"[red]✗ Failed to archive: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Project name to update")],
) -> None:
    """
    🔄 Update a project from its template.

    Supports:
    - Copier (preferred): Runs 'copier update'
    - Legacy: Checks if hydration is possible (warns mainly)
    """
    from devbase.utils.telemetry import get_telemetry

    root: Path = ctx.obj["root"]
    telemetry = get_telemetry(root)

    project_path = root / "20-29_CODE" / "21_monorepo_apps" / name

    if not project_path.exists():
        console.print(f"[red]✗ Project '{name}' not found[/red]")
        raise typer.Exit(1)

    console.print()
    console.print(Panel.fit(
        f"[bold blue]Update Project[/bold blue]\n\n"
        f"Project: [cyan]{name}[/cyan]",
        border_style="blue"
    ))

    copier_answers = project_path / ".copier-answers.yml"
    copier_answers_alt = project_path / ".copier-answers.yaml"

    if copier_answers.exists() or copier_answers_alt.exists():
        console.print("[dim]Detected Copier project. Running update...[/dim]")

        try:
            import copier

            copier.run_update(
                dst_path=str(project_path),
                unsafe=True,
                overwrite=True,
                quiet=False
            )

            console.print(f"[green]✓[/green] Project updated successfully!")
            telemetry.track(f"Updated project {name}", category="lifecycle", action="update_project", status="success")

        except ImportError:
            console.print("[red]✗ Copier not installed.[/red]")
            telemetry.track(f"Update failed {name}: copier missing", category="lifecycle", action="update_project", status="error")
        except OSError as e:
            console.print(f"[red]✗ Update failed: {e}[/red]")
            telemetry.track(f"Update failed {name}: {e}", category="lifecycle", action="update_project", status="error")

    else:
        console.print("[yellow]⚠ Not a Copier project.[/yellow]")
        console.print("Legacy template hydration is strongly discouraged for manual updates.")
        console.print("Recommendation: Migrate to Copier for update capabilities.")
        telemetry.track(f"Update skipped {name}", category="lifecycle", action="update_project", status="skipped")
