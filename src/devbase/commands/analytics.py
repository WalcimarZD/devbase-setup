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
    events_file = root / ".telemetry" / "events.jsonl"
    
    if not events_file.exists():
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
        con = duckdb.connect(database=':memory:')
        con.execute(f"CREATE TABLE events AS SELECT * FROM read_json_auto('{events_file}')")
        
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

# ── Graphical Report Command ─────────────────────────────────────────
    try:
        import duckdb
    except ImportError:
        console.print("[red]Error: DuckDB not installed.[/red]")
        console.print("Run: [green]pip install duckdb[/green] or [green]uv add duckdb[/green]")
        return

    root: Path = ctx.obj["root"]
    events_file = root / ".telemetry" / "events.jsonl"

    if not events_file.exists():
        console.print("[yellow]⚠️  No telemetry data found[/yellow]")
        return

    # DuckDB Analysis
    con = duckdb.connect(database=':memory:')
    
    # Load data (handling both schema v1 and v2 is tricky in SQL directly if columns differ too much,
    # but we will try to select common fields or use read_json_auto flexibility)
    
    try:
        con.execute(f"CREATE TABLE raw_events AS SELECT * FROM read_json_auto('{events_file}')")
        
        # Standardize columns (Schema V2)
        # If schema v1, some cols might be missing. We check available cols.
        columns = [c[1] for c in con.execute("PRAGMA table_info(raw_events)").fetchall()]
        
        has_category = 'category' in columns
        has_type = 'type' in columns
        
        # Normalize to 'category'
        # We want to select "category" if available, else "type", but handle mixed rows where one might be null.
        # Construct a COALESCE clause based on available columns.
        
        cols_to_check = []
        if has_category: cols_to_check.append("category")
        if has_type: cols_to_check.append("type")
        
        if not cols_to_check:
            # Neither exists
            cat_expr = "'unknown' as category"
        else:
            # coalesce(category, type, 'unknown')
            cols_str = ", ".join(cols_to_check)
            cat_expr = f"coalesce({cols_str}, 'unknown') as category"

        # Safe Select
        # Cast timestamp to TIMESTAMP to ensure comparison works
        df = con.execute(f"""
            SELECT 
                timestamp,
                {cat_expr},
                coalesce(message, '') as message,
                'event_id' as event_id
            FROM raw_events
            WHERE CAST(timestamp AS TIMESTAMP) >= (current_date - INTERVAL 7 DAY)
        """).fetchdf()
        
        # Calculate Metrics
        total_events = len(df)
        focus_score = 85 # Placeholder logic for optimization later
        
        # Prepare JSON for Vega-Lite
        # Convert timestamp to ISO string for JSON serialization
        json_data = df.to_json(orient='records', date_format='iso')

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
