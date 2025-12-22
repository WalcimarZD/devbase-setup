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

@app.command()
def report(
    ctx: typer.Context,
    open_browser: Annotated[bool, typer.Option("--open", "-o", help="Open report in browser")] = True,
) -> None:
    """
    📈 Generate graphical analytics report using DuckDB.
    """
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
        if has_category:
            cat_expr = "category"
        elif has_type:
            cat_expr = "type as category"
        else:
            cat_expr = "'unknown' as category"

        # Safe Select
        df = con.execute(f"""
            SELECT 
                timestamp,
                {cat_expr},
                coalesce(message, '') as message,
                'event_id' as event_id
            FROM raw_events
            WHERE timestamp >= (current_date - INTERVAL 7 DAY)
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

        output_path = root / "analytics_report.html"
        output_path.write_text(html, encoding='utf-8')

        console.print(f"[green]✓[/green] Report generated: [bold]{output_path}[/bold]")
        
        if open_browser:
            webbrowser.open(output_path.as_uri())

    except Exception as e:
        console.print(f"[red]Analytics Error: {e}[/red]")
        if "raw_events" in str(e): # Maybe empty file
             console.print("[yellow]Could not process events file. Is it empty?[/yellow]")
