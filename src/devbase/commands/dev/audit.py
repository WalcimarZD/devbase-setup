"""
Audit Commands
===============
Workspace naming convention audit.
"""
import re
from pathlib import Path

import typer
from rich.console import Console
from typing_extensions import Annotated

app = typer.Typer()
console = Console()


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

    allowed_patterns = [
        r'^\d{2}-\d{2}_',
        r'^\d{2}_',
        r'^[a-z0-9]+(-[a-z0-9]+)*$',
        r'^\d+(\.\d+)*$',
        r'^\.',
        r'^__',
        r'^src$',
        r'^tests?$',
        r'^docs?$',
        r'^lib$',
    ]

    default_ignore = [
        'node_modules', '.git', '__pycache__', 'bin', 'obj', '.vs',
        '.vscode', 'packages', 'vendor', 'dist', 'build', 'target',
        '.telemetry', '.devbase', 'credentials', 'local', 'cloud',
        'src', 'tests', 'test', 'docs', 'lib', 'scripts',
        'application', 'domain', 'infrastructure', 'presentation',
        'entities', 'value-objects', 'repositories', 'services', 'events',
        'use-cases', 'dtos', 'mappers', 'interfaces',
        'persistence', 'migrations', 'external', 'messaging',
        'api', 'cli', 'web', 'unit', 'integration', 'e2e',
        'ISSUE_TEMPLATE',
    ]

    violations = []

    with console.status("[bold cyan]Auditing workspace...[/bold cyan]"):
        for item in root.rglob('*'):
            if not item.is_dir():
                continue

            name = item.name

            if name in default_ignore:
                continue

            rel_parts = item.relative_to(root).parts
            if any(part in default_ignore for part in rel_parts):
                continue

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
                except OSError as e:
                    console.print(f"  [red]✗[/red] Failed: {v['name']} - {e}")
