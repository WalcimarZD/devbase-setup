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

    # Validate project name (kebab-case)
    if not re.match(r'^[a-z0-9]+([-.][a-z0-9]+)*$', name):
        from rich.prompt import Confirm

        console.print(f"[red]✗ Project name '{name}' is not kebab-case.[/red]")

        # Suggest valid name
        suggestion = re.sub(r'([a-z])([A-Z])', r'\1-\2', name).lower()
        suggestion = re.sub(r'[_ ]', '-', suggestion)
        # Remove any remaining invalid chars (keep only a-z, 0-9, -)
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

    # Use template engine
    from devbase.utils.templates import generate_project_from_template, list_available_templates
    from devbase.services.project_setup import get_project_setup
    from devbase.utils.telemetry import get_telemetry
    from devbase.services.adr_generator import get_ghostwriter

    telemetry = get_telemetry(root)
    setup_service = get_project_setup(root)

    # Start tracking
    telemetry.track(
        f"Creating project {name}",
        category="scaffolding",
        action="create_project_start",
        metadata={"template": template, "interactive": interactive}
    )

    try:
        console.print()
        console.print(f"[bold]Creating project '{name}'...[/bold]\n")

        # 1. Generate Files
        dest_path = generate_project_from_template(
            template_name=template,
            project_name=name,
            root=root,
            interactive=interactive
        )
        console.print(f"[green]✓[/green] Files generated at {dest_path}")

        # 2. Golden Path Setup
        if setup:
            setup_service.run_golden_path(dest_path, name)
        else:
            console.print("\n[dim]Skipping setup steps (--no-setup)[/dim]")
            console.print(f"\nNext steps:\n  cd {dest_path}\n  git init\n  code .")

        console.print(Panel.fit(
            f"[bold green]✅ Project Ready![/bold green]\n\n"
            f"Location: [cyan]{dest_path}[/cyan]",
            border_style="green"
        ))
        
        # Success telemetry
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
    from datetime import datetime
    from rich.prompt import Confirm
    from devbase.utils.telemetry import get_telemetry

    root: Path = ctx.obj["root"]
    telemetry = get_telemetry(root)

    project_path = root / "20-29_CODE" / "21_monorepo_apps" / name
    
    if not project_path.exists():
        console.print(f"[red]✗ Project '{name}' not found at {project_path}[/red]")
        raise typer.Exit(1)

    # Determine archive destination
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

    except Exception as e:
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
    import shutil
    import subprocess
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

    # check for copier
    copier_answers = project_path / ".copier-answers.yml"
    copier_answers_alt = project_path / ".copier-answers.yaml"
    
    if copier_answers.exists() or copier_answers_alt.exists():
        console.print("[dim]Detected Copier project. Running update...[/dim]")
        
        try:
             # Using subprocess to leverage copier CLI or we could import copier
             # importing copier is safer for python usage if installed
             import copier
             
             # Copier update typically needs to run inside the project root or specify it
             # copier.run_update(project_path) is not exactly the API, usually it's run_update(src_path, dst_path...)
             # But for update, we just need the destination if answers file exists.
             # API: copier.run_update(dst_path=..., ...)
             
             copier.run_update(
                 dst_path=str(project_path),
                 unsafe=True, # We trust our templates
                 overwrite=True,
                 quiet=False
             )
             
             console.print(f"[green]✓[/green] Project updated successfully!")
             telemetry.track(f"Updated project {name}", category="lifecycle", action="update_project", status="success")

        except ImportError:
             console.print("[red]✗ Copier not installed.[/red]")
             telemetry.track(f"Update failed {name}: copier missing", category="lifecycle", action="update_project", status="error")
        except Exception as e:
             console.print(f"[red]✗ Update failed: {e}[/red]")
             telemetry.track(f"Update failed {name}: {e}", category="lifecycle", action="update_project", status="error")
             
    else:
        # Legacy/Unknown
        console.print("[yellow]⚠ Not a Copier project.[/yellow]")
        console.print("Legacy template hydration is strongly discouraged for manual updates.")
        console.print("Recommendation: Migrate to Copier for update capabilities.")
        telemetry.track(f"Update skipped {name}", category="lifecycle", action="update_project", status="skipped")


@app.command(name="blueprint")
def blueprint(
    ctx: typer.Context,
    description: Annotated[str, typer.Argument(help="Descrição do projeto (ex: 'API FastAPI com Redis')")],
) -> None:
    """
    🏗️ Generate Dynamic Project Blueprint (IA).

    Usa IA para gerar uma estrutura de projeto baseada na descrição,
    inspirada em Clean Architecture.
    """
    import json
    from rich.tree import Tree
    from rich.prompt import Confirm
    from devbase.adapters.ai.groq_adapter import GroqProvider
    from devbase.services.security.sanitizer import sanitize_context
    from devbase.services.project_setup import get_project_setup

    root: Path = ctx.obj["root"]

    console.print()
    console.print(Panel.fit(
        f"[bold blue]DevBase Blueprint Generator[/bold blue]\n\n"
        f"Request: [cyan]{description}[/cyan]",
        border_style="blue"
    ))

    provider = GroqProvider()

    # Prompt for the AI
    # We want a JSON structure: {"files": [{"path": "src/main.py", "content": "..."}]}
    # We enforce Clean Arch inspiration.
    prompt = f"""
Generate a project file structure for: "{description}".
Follow Clean Architecture principles (Domain, Use Cases, Interfaces, Infrastructure).
Return ONLY a valid JSON object with this exact schema:
{{
  "project_name": "suggested-kebab-name",
  "files": [
    {{
      "path": "relative/path/to/file.ext",
      "content": "Minimal content/stub code..."
    }}
  ]
}}
Do not include markdown blocks or extra text.
"""

    with console.status("[bold green]🤖 Generating Blueprint...[/bold green]"):
        try:
            response = provider.generate(prompt, temperature=0.2, model="llama-3.3-70b-versatile")
            # Cleanup potential markdown fencing
            raw_json = response.content.strip()
            if raw_json.startswith("```"):
                raw_json = raw_json.strip("`").replace("json", "").strip()

            plan = json.loads(raw_json)
        except Exception as e:
            console.print(f"[red]Failed to generate blueprint: {e}[/red]")
            raise typer.Exit(1)

    project_name = plan.get("project_name", "unnamed-project")
    files = plan.get("files", [])

    # Preview using Rich Tree
    tree = Tree(f"📂 [bold cyan]{project_name}[/bold cyan]")

    # Group by directories for display
    # (Simple flat list to tree conversion for visualization)
    target_dir = root / "20-29_CODE" / "21_monorepo_apps" / project_name

    if target_dir.exists():
         console.print(f"[red]Error: Project '{project_name}' already exists at {target_dir}[/red]")
         raise typer.Exit(1)

    for f in files:
        tree.add(f"[green]📄 {f['path']}[/green]")

    console.print(tree)
    console.print()

    if Confirm.ask("[bold]Confirmar criação desta estrutura?[/bold]", default=True):
        console.print(f"\n[dim]Writing to {target_dir}...[/dim]")
        target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            path = target_dir / f['path']
            content = f['content']

            # Security check
            # We don't want to overwrite anything outside target_dir
            # sanitizer is for content, but we need path safety here.
            try:
                # Resolve ensures it's absolute
                # relative_to ensures it's inside target_dir
                full_path = (target_dir / path).resolve()
                full_path.relative_to(target_dir.resolve())

                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
                console.print(f"  [green]✓[/green] {path}")
            except Exception as e:
                console.print(f"  [red]✗[/red] Skipped unsafe path {path}: {e}")

        console.print(f"\n[bold green]✅ Project '{project_name}' created successfully![/bold green]")

        # Optional: Run Golden Path Setup?
        if Confirm.ask("Run Golden Path setup? (Git init, venv)", default=True):
            setup_service = get_project_setup(root)
            setup_service.run_golden_path(target_dir, project_name)
    else:
        console.print("[yellow]Aborted.[/yellow]")


@app.command(name="adr-gen")
def adr_gen(
    ctx: typer.Context,
    context: Annotated[str, typer.Option("--context", "-c", help="Context or reasoning for the decision")] = "",
) -> None:
    """
    👻 Ghostwrite an ADR from recent activity.

    Analyses recent 'track' events or uses provided context to generate
    an Architecture Decision Record (MADR format).
    """
    root: Path = ctx.obj["root"]
    ghostwriter = get_ghostwriter(root)

    console.print()
    console.print("[bold]ADR Ghostwriter[/bold]")

    final_context = context

    # If no manual context, scan recent events
    if not final_context:
        console.print("[dim]Scanning recent architecture events...[/dim]")
        events = ghostwriter.find_recent_decisions()
        if events:
            console.print(f"[green]Found {len(events)} relevant events.[/green]")
            lines = [f"- {e['message']} ({e['timestamp']})" for e in events]
            final_context = "\n".join(lines)
        else:
            if not context:
                console.print("[yellow]No recent architecture events found.[/yellow]")
                from rich.prompt import Prompt
                final_context = Prompt.ask("Please provide context for the ADR")

    if final_context:
        path = ghostwriter.generate_draft(final_context)
        if path:
            console.print(Panel.fit(
                f"[bold green]✅ ADR Drafted![/bold green]\n\n"
                f"Location: [cyan]{path}[/cyan]\n"
                f"Review and edit before committing.",
                border_style="green"
            ))
        else:
            console.print("[red]Failed to generate ADR.[/red]")


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

    with console.status("[bold cyan]Auditing workspace...[/bold cyan]"):
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
