"""
Operations Commands: track, stats, weekly, backup, clean
=========================================================
Operational and productivity commands.
"""
import json
import shutil
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

app = typer.Typer(help="Operations & automation")
console = Console()


@app.command()
def track(
    ctx: typer.Context,
    message: Annotated[str, typer.Argument(help="Activity message")],
    event_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Event type (auto-detected if not specified)"),
    ] = None,
) -> None:
    """
    📝 Track an activity or task.
    
    Logs activities to telemetry for later analysis with stats/weekly commands.
    
    AUTO-DETECTION:
    - If you're inside a project folder, it auto-tags with project name
    - Activity type is inferred from your location:
      * code/packages → "coding"
      * knowledge → "learning"
      * vault → "personal"
      * ai → "ai"
    
    Example:
        cd 20-29_CODE/21_monorepo_apps/my-api
        devbase ops track "Implemented OAuth2"
        # → Auto-tagged as: [coding:my-api]
    """
    root: Path = ctx.obj["root"]

    from devbase.utils.telemetry import get_telemetry
    
    telemetry = get_telemetry(root)
    event = telemetry.track(
        message=message,
        category=event_type
    )

    console.print(f"[green]✓[/green] Tracked: [[cyan]{event['metadata']['category']}[/cyan]] {message}")


@app.command()
def stats(ctx: typer.Context) -> None:
    """
    📊 Show activity statistics.
    
    Displays summary of tracked activities by type and recent events.
    """
    root: Path = ctx.obj["root"]
    events_file = root / ".telemetry" / "events.jsonl"

    if not events_file.exists():
        console.print("[yellow]⚠️  No telemetry data found[/yellow]")
        console.print("[dim]Run 'devbase ops track \"message\"' to start tracking.[/dim]")
        return

    # Load events
    events = []
    with open(events_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not events:
        console.print("[yellow]⚠️  No events recorded[/yellow]")
        return

    console.print()
    console.print("[bold]Activity Statistics[/bold]")
    console.print(f"Total events: [cyan]{len(events)}[/cyan]\n")

    # Count by type
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    # 1. Analyze Telemetry (New)
    # from collections import Counter # Already imported
    # import json # Already imported
    
    telemetry_file = root / ".telemetry" / "events.jsonl"
    
    project_creates = 0
    templates_used = Counter()
    
    if telemetry_file.exists():
        try:
            with open(telemetry_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("action") == "create_project_success":
                            project_creates += 1
                            # Try to extract template from metadata if present
                            # We might need to look back at the start event for template info
                            # or update success event to include it. 
                            # For simplicity, let's assume metadata has it or we just count generic success
                            # If metadata has path, we can't infer template easily without looking detailed
                            pass
                        
                        # Better approach: check create_project_start for template popularity
                        if event.get("action") == "create_project_start":
                            tmpl = event.get("metadata", {}).get("template", "unknown")
                            templates_used[tmpl] += 1
                            
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    # Display Metrics
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column(justify="right")
    
    grid.add_row("[bold]Weekly Activity[/bold]", "")
    grid.add_row("Projects Created (Total)", f"[cyan]{project_creates}[/cyan]")
    
    if templates_used:
        grid.add_row("", "")
        grid.add_row("[bold]Popular Templates[/bold]", "")
        for tmpl, count in templates_used.most_common(3):
            grid.add_row(f"  {tmpl}",str(count))

    console.print(Panel(grid, title="DevBase Stats", border_style="blue"))
    console.print()

    # Original "Count by type" logic, adapted to be "Weekly Log"
    type_counts = Counter(e.get("category") or e.get("type", "unknown") for e in events)
    table = Table(title="Events by Type") # Changed title to "Events by Type" to match original intent
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right", style="green")

    for event_type, count in type_counts.most_common():
        table.add_row(event_type, str(count))

    console.print(table)

    # Recent activity
    console.print()
    console.print("[bold]Recent Activity:[/bold]")
    for event in events[-5:]:
        ts = event.get("timestamp", "")[:10]
        msg = event.get("message", "")[:60]
        console.print(f"  [dim]{ts}[/dim] {msg}")


@app.command()
def weekly(
    ctx: typer.Context,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Save report to file (relative to workspace)"),
    ] = None,
) -> None:
    """
    📅 Generate weekly activity report.
    
    Creates a markdown report of the last 7 days of activities.
    
    Output paths are relative to workspace by default:
    - No --output: saves to journal/weekly-YYYY-MM-DD.md
    - --output report.md: saves to journal/report.md
    - --output C:\\path\\report.md: saves to absolute path (escapes workspace)
    """
    from devbase.utils.paths import resolve_workspace_path
    
    root: Path = ctx.obj["root"]
    events_file = root / ".telemetry" / "events.jsonl"

    if not events_file.exists():
        console.print("[yellow]⚠️  No telemetry data found[/yellow]")
        return

    # Filter last week
    week_ago = datetime.now() - timedelta(days=7)
    events = []

    with open(events_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    event = json.loads(line)
                    ts = datetime.fromisoformat(event.get("timestamp", ""))
                    if ts >= week_ago:
                        events.append(event)
                except (json.JSONDecodeError, ValueError):
                    pass

    # Generate report
    report = f"""# Weekly Report

**Period**: {week_ago.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}  
**Total activities**: {len(events)}

## Activities

"""
    for event in events:
        ts = event.get("timestamp", "")[:10]
        msg = event.get("message", "")
        # v2 uses 'category', v1 uses 'type'
        cat = event.get("category") or event.get("type", "unknown")
        # Ensure project is shown if available (v2 context)
        ctx_data = event.get("context", {})
        if isinstance(ctx_data, dict) and ctx_data.get("project"):
            cat = f"{cat}:{ctx_data['project']}"
            
        report += f"- [{ts}] **{cat}**: {msg}\n"

    # Determine output path (workspace-relative by default)
    default_subdir = "10-19_KNOWLEDGE/12_private_vault/journal"
    
    if output is None:
        # Auto-generate filename
        filename = f"weekly-{datetime.now().strftime('%Y-%m-%d')}.md"
        final_path = root / default_subdir / filename
    else:
        final_path = resolve_workspace_path(output, root, default_subdir)
    
    # Ensure directory exists
    final_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    final_path.write_text(report, encoding="utf-8")
    console.print(f"[green]✓[/green] Report saved to: [cyan]{final_path}[/cyan]")


@app.command()
def backup(ctx: typer.Context) -> None:
    """
    💾 Create workspace backup (3-2-1 strategy).
    
    Creates a local backup excluding common build artifacts.
    """
    root: Path = ctx.obj["root"]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"devbase_backup_{timestamp}"
    backup_dir = root / "30-39_OPERATIONS" / "31_backups" / "local"
    backup_path = backup_dir / backup_name

    console.print()
    console.print("[bold]Creating backup...[/bold]")
    console.print(f"Location: [cyan]{backup_path}[/cyan]\n")

    # Exclusions (build artifacts + SECURITY: secrets/credentials)
    exclude = {
        # Build artifacts
        'node_modules', '.git', '31_backups', '__pycache__', '.vs', 'bin', 'obj',
        '.venv', 'venv', 'dist', 'build', '.pytest_cache', '.mypy_cache',
        '.ruff_cache', '.coverage', 'htmlcov',
        # SECURITY: Secret files (prevent credential leakage)
        '.env', '.env.local', '.env.production', '.env.development',
        '.pypirc', '.npmrc', '.aws', '.ssh', '.gnupg',
        # Note: Individual secret files with extensions are handled by pattern matching below
    }
    
    # Additional patterns for secret files
    secret_patterns = {'.pem', '.key', '.p12', '.pfx', 'id_rsa', 'id_ed25519', '.crt'}

    def ignore_patterns(dir, files):
        ignored = []
        for f in files:
            # Directory-level exclusions
            if f in exclude:
                ignored.append(f)
                continue
            # File extension patterns (secrets)
            if any(f.endswith(pattern) or f == pattern for pattern in secret_patterns):
                ignored.append(f)
        return ignored

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, backup_path, ignore=ignore_patterns)

        # Calculate size
        size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
        size_mb = size / (1024 * 1024)

        console.print("[green]✓[/green] Backup created successfully")
        console.print(f"  Size: [cyan]{size_mb:.2f} MB[/cyan]")
    except Exception as e:
        console.print(f"[red]✗ Backup failed: {e}[/red]")


@app.command()
def clean(ctx: typer.Context) -> None:
    """
    🧹 Clean temporary files from workspace.
    
    Removes common temporary file patterns (*.log, *.tmp, etc.).
    """
    root: Path = ctx.obj["root"]

    console.print()
    console.print("[bold]Cleaning temporary files...[/bold]\n")

    patterns = ['*.log', '*.tmp', '*~', 'Thumbs.db', '.DS_Store']
    cleaned = 0

    for pattern in patterns:
        for file in root.rglob(pattern):
            if file.is_file():
                try:
                    file.unlink()
                    cleaned += 1
                    console.print(f"  [dim]Removed: {file.name}[/dim]")
                except Exception:
                    pass

    console.print()
    console.print(f"[green]✓[/green] Removed {cleaned} temporary file(s)")
