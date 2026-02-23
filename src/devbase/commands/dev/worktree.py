"""
Worktree Commands
==================
Git worktree management for parallel development.
"""
import json
import logging
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


@app.command(name="worktree-add")
def worktree_add(
    ctx: typer.Context,
    project_name: Annotated[str, typer.Argument(help="Parent project name")],
    branch: Annotated[str, typer.Argument(help="Branch name to checkout")],
    create: Annotated[
        bool,
        typer.Option("--create", "-c", help="Create new branch")
    ] = False,
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Custom worktree folder name")
    ] = None,
) -> None:
    """
    🌳 Create a new worktree for a project.

    Creates a worktree in 22_worktrees/<project>-<branch> (default).

    Examples:
        devbase dev worktree-add MedSempreMVC_GIT feature/nova-rotina
        devbase dev worktree-add MyProject feature/xyz --create
        devbase dev worktree-add MyProject feature/xyz --name "my-feature-xyz"
    """
    from devbase.utils.worktree import add_worktree, get_worktree_dir
    from devbase.utils.vscode import generate_vscode_workspace

    root: Path = ctx.obj["root"]
    project_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name

    if not project_path.exists():
        console.print(f"[red]✗ Project '{project_name}' not found.[/red]")
        raise typer.Exit(1)

    if not (project_path / ".git").exists():
        console.print(f"[red]✗ Project '{project_name}' is not a git repository.[/red]")
        raise typer.Exit(1)

    worktrees_dir = get_worktree_dir(root)
    worktree_path = add_worktree(project_path, worktrees_dir, project_name, branch, create, custom_name=name)

    if worktree_path:
        generate_vscode_workspace(worktree_path, worktree_path.name)

        console.print(Panel(
            f"[bold green]✅ Worktree created![/bold green]\n\n"
            f"Location: [cyan]{worktree_path}[/cyan]\n"
            f"Branch: [yellow]{branch}[/yellow]\n\n"
            f"Open with: [dim]devbase dev open {worktree_path.name}[/dim]",
            border_style="green"
        ))


@app.command(name="worktree-list")
def worktree_list(
    ctx: typer.Context,
    project_name: Annotated[str, typer.Argument(help="Project name to list worktrees for")] = None,
) -> None:
    """
    🌳 List worktrees for a project or all projects.

    Examples:
        devbase dev worktree-list
        devbase dev worktree-list MedSempreMVC_GIT
    """
    from devbase.utils.worktree import list_worktrees

    root: Path = ctx.obj["root"]
    apps_dir = root / "20-29_CODE" / "21_monorepo_apps"

    if project_name:
        projects = [apps_dir / project_name]
        if not projects[0].exists():
            console.print(f"[red]✗ Project '{project_name}' not found.[/red]")
            raise typer.Exit(1)
    else:
        projects = [p for p in apps_dir.iterdir() if p.is_dir() and (p / ".git").exists()]

    table = Table(title="Git Worktrees", show_header=True, header_style="bold magenta")
    table.add_column("Project", style="cyan")
    table.add_column("Branch", style="yellow")
    table.add_column("Path")
    table.add_column("Commit", style="dim")

    total = 0
    for project in sorted(projects, key=lambda x: x.name):
        worktrees = list_worktrees(project)
        for wt in worktrees:
            if Path(wt["path"]) == project:
                continue
            table.add_row(
                project.name,
                wt.get("branch", "(detached)"),
                Path(wt["path"]).name,
                wt.get("commit", "")
            )
            total += 1

    if total == 0:
        console.print("[dim]No worktrees found.[/dim]")
        console.print("\nCreate one with:\n  [cyan]devbase dev worktree-add <project> <branch>[/cyan]")
    else:
        console.print(table)
        console.print(f"\n[dim]Total: {total} worktrees[/dim]")


@app.command(name="worktree-remove")
def worktree_remove(
    ctx: typer.Context,
    worktree_name: Annotated[str, typer.Argument(help="Worktree name (from 22_worktrees/)")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force removal even with uncommitted changes")
    ] = False,
) -> None:
    """
    🌳 Remove a worktree.

    Examples:
        devbase dev worktree-remove MedSempreMVC_GIT--feature-xyz
        devbase dev worktree-remove MyProject--hotfix --force
    """
    import shutil
    from devbase.utils.worktree import remove_worktree, get_worktree_dir

    root: Path = ctx.obj["root"]
    worktrees_dir = get_worktree_dir(root)
    worktree_path = worktrees_dir / worktree_name

    if not worktree_path.exists():
        console.print(f"[red]✗ Worktree '{worktree_name}' not found.[/red]")
        raise typer.Exit(1)

    project_name = None
    meta_file = worktree_path / ".devbase.json"

    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            project_name = meta.get("parent_project")
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Could not read worktree metadata: {e}")

    if not project_name:
        project_name = worktree_name.split("--")[0]
    project_path = root / "20-29_CODE" / "21_monorepo_apps" / project_name

    if not project_path.exists():
        console.print(f"[yellow]⚠ Parent project '{project_name}' not found. Removing directory only.[/yellow]")
        shutil.rmtree(worktree_path)
        console.print(f"[green]✓[/green] Removed worktree directory: {worktree_name}")
        return

    success = remove_worktree(project_path, worktree_path, force)
    if not success:
        raise typer.Exit(1)
