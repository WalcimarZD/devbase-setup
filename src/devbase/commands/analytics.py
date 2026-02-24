"""
Analytics Command: generate reports
===================================
Generates personal productivity reports using DuckDB.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import webbrowser

import typer
from rich.console import Console
from typing_extensions import Annotated

app = typer.Typer(help="Analytics & Insights")
console = Console()

REPORT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <title>DevBase Analytics</title>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 20px; max-width: 1200px; margin: 0 auto; background: #f9f9f9; }
    h1 { color: #333; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
    .stat { font-size: 2em; font-weight: bold; color: #2c3e50; }
    .label { color: #7f8c8d; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
  </style>
</head>
<body>
  <h1>🚀 Personal Productivity Report</h1>
  <p>Generated on: {{ GENERATED_AT }}</p>

  <div class="grid">
    <div class="card">
      <div class="label">Total Activities (Last 7 Days)</div>
      <div class="stat">{{ TOTAL_EVENTS }}</div>
    </div>
    <div class="card">
      <div class="label">Focus Score</div>
      <div class="stat">{{ FOCUS_SCORE }}%</div>
    </div>
  </div>

  <div class="card">
    <h2>Weekly Flow</h2>
    <div id="vis-flow"></div>
  </div>

  <div class="card">
    <h2>Category Breakdown</h2>
    <div id="vis-category"></div>
  </div>

  <script type="text/javascript">
    const data = {{ DATA_JSON }};

    const flowSpec = {
      "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
      "description": "Activity intensity over time.",
      "data": { "values": data },
      "mark": "bar",
      "encoding": {
        "x": {"field": "timestamp", "type": "temporal", "timeUnit": "dayhours"},
        "y": {"aggregate": "count", "title": "Intensity"},
        "color": {"field": "category", "type": "nominal"}
      },
      "width": "container"
    };
    vegaEmbed('#vis-flow', flowSpec);

    const catSpec = {
      "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
      "data": { "values": data },
      "mark": "arc",
      "encoding": {
        "theta": {"aggregate": "count", "field": "event_id"},
        "color": {"field": "category", "type": "nominal"}
      }
    };
    vegaEmbed('#vis-category', catSpec);
  </script>
</body>
</html>
"""

from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# ── Terminal Summary Logic ──────────────────────────────────────────

def show_terminal_summary(root: Path):
    """Shows a quick productivity dashboard in the terminal."""
    from devbase.adapters.storage.duckdb_adapter import get_db_path
    db_path = get_db_path(root)
    
    if not db_path.exists():
        console.print(Panel(
            "[yellow]No telemetry data found yet.[/yellow]\n\n"
            "To start tracking your productivity, use:\n"
            "[cyan]devbase ops track \"Finished feature X\"[/cyan]",
            title="📈 Analytics",
            border_style="yellow"
        ))
        return

    try:
        import duckdb
        con = duckdb.connect(database=str(db_path), read_only=True)
        
        # Simple aggregation for terminal
        summary = con.execute("""
            SELECT 
                count(*) as total,
                count(DISTINCT strftime(timestamp, '%Y-%m-%d')) as days
            FROM events
            WHERE CAST(timestamp AS TIMESTAMP) >= (current_date - INTERVAL 7 DAY)
        """).fetchone()
        
        total_last_week = summary[0]
        active_days = summary[1]

        table = Table(title="Weekly Activity", show_header=True, header_style="bold magenta", box=None)
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="bold")
        
        table.add_row("Events (Last 7d)", str(total_last_week))
        table.add_row("Active Days", f"{active_days}/7")
        
        console.print(Panel(table, title="🚀 Productivity Overview", border_style="blue", expand=False))
        console.print("[dim]Tip: Use 'devbase analytics report' for a full graphical view.[/dim]")
        
    except Exception:
        console.print("[red]✗ Could not parse telemetry data.[/red]")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """📈 Workspace Productivity Insights."""
    if ctx.invoked_subcommand is None:
        root: Path = ctx.obj["root"]
        show_terminal_summary(root)

@app.command()
def report(
    ctx: typer.Context,
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open the report in the browser automatically")] = True,
):
    """📊 [bold]Generate a full graphical productivity report.[/bold]"""
    try:
        import duckdb
    except ImportError:
        console.print("[red]Error: DuckDB not installed.[/red]")
        console.print("Run: [green]pip install duckdb[/green] or [green]uv add duckdb[/green]")
        return

    from devbase.adapters.storage.duckdb_adapter import get_db_path
    db_path = get_db_path(root)

    if not db_path.exists():
        console.print("[yellow]⚠️  No telemetry database found[/yellow]")
        return

    # DuckDB Analysis
    con = duckdb.connect(database=str(db_path), read_only=True)
    
    try:
        # Standardize columns (Schema V2)
        # Using the existing 'events' table
        columns = [c[1] for c in con.execute("PRAGMA table_info(events)").fetchall()]
        
        has_category = 'category' in columns
        has_type = 'event_type' in columns
        
        # Normalize to 'category'
        cols_to_check = []
        if 'metadata' in columns:
            # We can extract from JSON metadata if needed, but let's stick to columns for now
            pass
        
        cat_expr = "event_type as category" # Simple mapping for now

        # Safe Select
        rows = con.execute(f"""
            SELECT 
                timestamp,
                {cat_expr},
                coalesce(message, '') as message,
                'event_id' as event_id
            FROM events
            WHERE CAST(timestamp AS TIMESTAMP) >= (current_date - INTERVAL 7 DAY)
        """).fetchall()
        
        # Calculate Metrics
        total_events = len(rows)
        focus_score = 85 # Placeholder logic for optimization later
        
        # Prepare JSON for Vega-Lite
        import json
        records = []
        for r in rows:
            records.append({
                "timestamp": r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0]),
                "category": r[1],
                "message": r[2],
                "event_id": r[3]
            })
        json_data = json.dumps(records)

        # Rendering
        html = REPORT_TEMPLATE.replace("{{ GENERATED_AT }}", datetime.now().strftime("%Y-%m-%d %H:%M"))
        html = html.replace("{{ TOTAL_EVENTS }}", str(total_events))
        html = html.replace("{{ FOCUS_SCORE }}", str(focus_score))
        html = html.replace("{{ DATA_JSON }}", json_data)

        # Save to semantic location (monitoring folder)
        output_dir = root / "30-39_OPERATIONS" / "33_monitoring"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "analytics_report.html"
        output_path.write_text(html, encoding='utf-8')

        console.print(f"[green]✓[/green] Report generated: [bold]{output_path}[/bold]")
        
        if open_browser:
            webbrowser.open(output_path.as_uri())

    except Exception as e:
        console.print(f"[red]Analytics Error: {e}[/red]")
        if "raw_events" in str(e): # Maybe empty file
             console.print("[yellow]Could not process events file. Is it empty?[/yellow]")
