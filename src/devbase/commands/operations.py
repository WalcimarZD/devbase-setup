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

    # Detect context
    from devbase.utils.context import detect_context, infer_activity_type, infer_project_name

    current_dir = Path.cwd()
    context = detect_context(current_dir, root)

    # Auto-infer type if not specified
    if not event_type:
        event_type = infer_activity_type(context)

        # Add project suffix if inside a project
        project = infer_project_name(context)
        if project:
            event_type = f"{event_type}:{project}"

    # Ensure telemetry directory
    telemetry_dir = root / ".telemetry"
    telemetry_dir.mkdir(exist_ok=True)
    events_file = telemetry_dir / "events.jsonl"

    # Create event
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "message": message,
        "context": context.get("context_type"),
    }

    # Append to file
    with open(events_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\\n")

    console.print(f"[green]✓[/green] Tracked: [[cyan]{event_type}[/cyan]] {message}")


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
    type_counts = Counter(e.get("type", "unknown") for e in events)

    table = Table(title="Events by Type")
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
        typer.Option("--output", "-o", help="Save report to file"),
    ] = None,
) -> None:
    """
    📅 Generate weekly activity report.
    
    Creates a markdown report of the last 7 days of activities.
    """
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
        report += f"- [{ts}] {msg}\\n"

    if output:
        output.write_text(report, encoding="utf-8")
        console.print(f"[green]✓[/green] Report saved to: [cyan]{output}[/cyan]")
    else:
        console.print(report)


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

    # Exclusions
    exclude = {'node_modules', '.git', '31_backups', '__pycache__', '.vs', 'bin', 'obj'}

    def ignore_patterns(dir, files):
        return [f for f in files if f in exclude]

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
