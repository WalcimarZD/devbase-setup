"""
Development Commands: new, audit
=================================
Commands for creating and managing code projects.
"""
import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from typing_extensions import Annotated

app = typer.Typer(help="Development commands")
console = Console()


@app.command()
def new(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Project name (kebab-case)")],
    template: Annotated[
        str,
        typer.Option("--template", "-t", help="Template name"),
    ] = "clean-arch",
    interactive: Annotated[
        bool,
        typer.Option("--interactive/--no-interactive", help="Customize project details"),
    ] = True,
) -> None:
    """
    📦 Create a new project from template.
    
    Creates a customized project in 21_monorepo_apps/ using the specified template.
    In interactive mode, prompts for description, license, and author.
    
    Templates support variable substitution:
    - {{project_name}} - Original name (kebab-case)
    - {{project_name_pascal}} - PascalCase version
    - {{project_name_snake}} - snake_case version
    - {{author}} - Author name (from git config)
    - {{year}} - Current year
    - {{description}} - Project description
    - {{license}} - License type
    
    Example:
        devbase dev new my-api              # Interactive prompts
        devbase dev new my-lib --no-interactive  # Use defaults
    """
    root: Path = ctx.obj["root"]

    # Validate project name (kebab-case)
    if not re.match(r'^[a-z0-9]+([-.][a-z0-9]+)*$', name):
        console.print("[red]✗ Project name must be in kebab-case (e.g., my-project)[/red]")
        raise typer.Exit(1)

    # Use template engine
    from devbase.utils.templates import generate_project_from_template, list_available_templates

    try:
        console.print()
        console.print(f"[bold]Creating project '{name}'...[/bold]\n")

        dest_path = generate_project_from_template(
            template_name=template,
            project_name=name,
            root=root,
            interactive=interactive
        )

        console.print()
        console.print(Panel.fit(
            f"[bold green]✅ Project created![/bold green]\n\n"
            f"Location: [cyan]{dest_path}[/cyan]\n\n"
            f"Next steps:\n"
            f"  1. [dim]cd {dest_path}[/dim]\n"
            f"  2. [dim]git init[/dim]\n"
            f"  3. [dim]code .[/dim]",
            border_style="green"
        ))
    except FileNotFoundError:
        console.print(f"[red]✗ Template '{template}' not found[/red]\n")
        console.print("Available templates:")
        for tmpl in list_available_templates(root):
            console.print(f"  [cyan]• {tmpl}[/cyan]")
        raise typer.Exit(1)
    except FileExistsError:
        console.print(f"[red]✗ Project '{name}' already exists[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Failed to create project: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def audit(
    ctx: typer.Context,
    fix: Annotated[
        bool,
        typer.Option("--fix", help="Automatically fix violations"),
    ] = False,
) -> None:
    """
    🔍 Audit workspace naming conventions (kebab-case).
    
    Scans all directories and reports violations of the kebab-case
    naming convention required by DevBase.
    """
    root: Path = ctx.obj["root"]

    console.print()
    console.print("[bold]Auditing naming conventions...[/bold]")
    console.print(f"Workspace: [cyan]{root}[/cyan]\n")


    # Allowed patterns - IMPORTANT: Use raw strings (r"") for regex
    allowed_patterns = [
        r'^\d{2}-\d{2}_',                 # Johnny.Decimal areas (00-09_SYSTEM)
        r'^\d{2}_',                       # Johnny.Decimal categories (00_inbox, 21_monorepo_apps)
        r'^[a-z0-9]+(-[a-z0-9]+)*$',      # kebab-case (my-project)
        r'^\d+(\.\d+)*$',                 # Versions (4.0.3)
        r'^\.',                           # Dotfiles (.git, .vscode)
        r'^__',                           # Dunder (__pycache__, __template-*)
        r'^src$',                         # Common code folders
        r'^tests?$',                      # test or tests
        r'^docs?$',                       # doc or docs
        r'^lib$',                         # lib folder
    ]

    # Ignore patterns - folders to skip entirely
    default_ignore = [
        'node_modules', '.git', '__pycache__', 'bin', 'obj', '.vs',
        '.vscode', 'packages', 'vendor', 'dist', 'build', 'target',
        '.telemetry', '.devbase', 'credentials', 'local', 'cloud',
        # Standard code structure folders
        'src', 'tests', 'test', 'docs', 'lib', 'scripts',
        'application', 'domain', 'infrastructure', 'presentation',
        'entities', 'value-objects', 'repositories', 'services', 'events',
        'use-cases', 'dtos', 'mappers', 'interfaces',
        'persistence', 'migrations', 'external', 'messaging',
        'api', 'cli', 'web', 'unit', 'integration', 'e2e',
        # Template internals
        'ISSUE_TEMPLATE',
    ]

    violations = []

    for item in root.rglob('*'):
        if not item.is_dir():
            continue

        name = item.name

        # Check if should ignore
        if name in default_ignore:
            continue
        
        # Skip anything inside known good structures
        rel_parts = item.relative_to(root).parts
        if any(part in default_ignore for part in rel_parts):
            continue

        # Check if name matches allowed patterns
        is_allowed = any(re.match(pattern, name) for pattern in allowed_patterns)

        if not is_allowed:
            suggestion = re.sub(r'([a-z])([A-Z])', r'\1-\2', name).lower()
            suggestion = re.sub(r'[_ ]', '-', suggestion)
            violations.append({
                'path': item,
                'name': name,
                'suggestion': suggestion
            })

    if not violations:
        console.print("[bold green]✅ No violations found[/bold green]")
    else:
        console.print(f"[yellow]Found {len(violations)} violation(s):[/yellow]\n")

        for v in violations[:20]:
            console.print(f"  [red]✗[/red] {v['name']}")
            console.print(f"    [dim]→ Suggested: {v['suggestion']}[/dim]")
            console.print(f"    [dim]  Path: {v['path']}[/dim]\n")

        if len(violations) > 20:
            console.print(f"[dim]... and {len(violations) - 20} more violations[/dim]\n")

        if fix:
            console.print("[bold]Applying fixes...[/bold]")
            for v in violations:
                try:
                    new_path = v['path'].parent / v['suggestion']
                    v['path'].rename(new_path)
                    console.print(f"  [green]✓[/green] Renamed: {v['name']} → {v['suggestion']}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed: {v['name']} - {e}")
