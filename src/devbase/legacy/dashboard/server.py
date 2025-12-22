"""
DevBase Dashboard Server
================================================================
A minimal Flask server for visualizing telemetry data.

Usage:
    python -m dashboard.server
    # Or via CLI:
    devbase dashboard

Author: DevBase Team
Version: 3.2.0
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

try:
    from flask import Flask, jsonify, render_template, request
except ImportError:
    print("Flask is required for the dashboard. Install with: pip install flask")
    sys.exit(1)

app = Flask(__name__, 
    template_folder="templates",
    static_folder="static"
)

# DevBase root detection
def get_devbase_root() -> Path:
    """Detect DevBase root from environment or current directory."""
    if "DEVBASE_ROOT" in os.environ:
        return Path(os.environ["DEVBASE_ROOT"])
    
    # Try to find .devbase_state.json
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".devbase_state.json").exists():
            return parent
    
    return Path.home() / "Dev_Workspace"


def load_events(root: Path, days: int = 30):
    """Load telemetry events from the last N days."""
    events_file = root / ".telemetry" / "events.jsonl"
    if not events_file.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=days)
    events = []
    
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                ts = datetime.fromisoformat(event.get("timestamp", ""))
                if ts >= cutoff:
                    event["date"] = ts.strftime("%Y-%m-%d")
                    events.append(event)
            except (json.JSONDecodeError, ValueError):
                pass
    
    return events


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/api/stats")
def api_stats():
    """Return aggregated statistics."""
    root = get_devbase_root()
    days = request.args.get("days", 30, type=int)
    events = load_events(root, days)
    
    # Aggregate by type
    type_counts = Counter(e.get("type", "unknown") for e in events)
    
    # Aggregate by date
    date_counts = Counter(e.get("date", "") for e in events)
    
    # Sort dates
    sorted_dates = sorted(date_counts.keys())
    
    return jsonify({
        "total": len(events),
        "by_type": dict(type_counts),
        "by_date": {
            "labels": sorted_dates,
            "values": [date_counts[d] for d in sorted_dates]
        },
        "recent": events[-10:][::-1]  # Last 10, newest first
    })


@app.route("/api/activity")
def api_activity():
    """Return activity list with pagination."""
    root = get_devbase_root()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    events = load_events(root, days=365)
    events = events[::-1]  # Newest first
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        "total": len(events),
        "page": page,
        "per_page": per_page,
        "items": events[start:end]
    })


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Start the dashboard server."""
    print(f"\n🚀 DevBase Dashboard running at http://{host}:{port}")
    print("   Press Ctrl+C to stop\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)
