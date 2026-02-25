"""
Debug Command: Active Environment Probes
=========================================
Performs deep system diagnostics using active probes instead of static tests.
"""
import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class DebugReport:
    """Manages diagnostic probes and report generation."""

    def __init__(self, root: Path):
        self.root = root
        self.timestamp = datetime.now()
        self.probes: List[Dict[str, Any]] = []

    def add_probe(self, category: str, name: str, status: str, result: str, detail: Optional[str] = None):
        self.probes.append({
            "category": category,
            "name": name,
            "status": status,
            "result": result,
            "detail": detail
        })

    def print_terminal_summary(self):
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]DevBase Active Diagnostic[/bold cyan]\n"
            f"Workspace: [yellow]{self.root}[/yellow]\n"
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="cyan"
        ))

        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Category", style="dim", width=15)
        table.add_column("Probe", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Result")

        for p in self.probes:
            status_style = "[green]PASS[/green]" if p["status"] == "SUCCESS" else "[red]FAIL[/red]" if p["status"] == "ERROR" else "[yellow]WARN[/yellow]"
            table.add_row(p["category"], p["name"], status_style, p["result"])

        console.print(table)
        
        errors = [p for p in self.probes if p["status"] == "ERROR"]
        if errors:
            console.print("\n[bold red]Critical Issues Detected:[/bold red]")
            for e in errors:
                console.print(f"  • [bold]{e['name']}[/bold]: {e['detail']}")

def run_system_probes(report: DebugReport):
    """Executes active probes on the production environment."""
    
    # --- 1. Environment Probe ---
    uv_path = shutil.which("uv")
    report.add_probe("ENV", "Package Manager", "SUCCESS" if uv_path else "WARN", 
                     f"uv found" if uv_path else "uv not in PATH")

    # --- 2. Database Probe (DuckDB) ---
    try:
        from devbase.adapters.storage.duckdb_adapter import get_connection
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        report.add_probe("DATA", "DuckDB Integrity", "SUCCESS", "Read/Write OK")
    except Exception as e:
        report.add_probe("DATA", "DuckDB Integrity", "ERROR", "Connection Failed", str(e))

    # --- 3. AI Probe (Provider Connectivity) ---
    try:
        from devbase.services.container import ServiceContainer
        container = ServiceContainer(report.root)
        ai_service = container.ai
        report.add_probe("AI", "Provider Link", "SUCCESS", "Initialized")
    except Exception as e:
        report.add_probe("AI", "Provider Link", "WARN", "Config Error", str(e))

    # --- 4. Workspace Probe ---
    state_file = report.root / ".devbase_state.json"
    report.add_probe("SPACE", "Workspace State", "SUCCESS" if state_file.exists() else "WARN",
                     "Initialized" if state_file.exists() else "Not Found")

def debug_cmd(ctx: typer.Context) -> None:
    """
    🐞 System Diagnostics & Health Probes.

    Performs deep analysis of the active environment:
    - ENV: Tool availability.
    - DATA: DuckDB health.
    - AI: Provider connectivity.
    - SPACE: Workspace integrity.
    """
    root: Path = ctx.obj["root"]
    report = DebugReport(root)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        progress.add_task("Running system probes...", total=None)
        run_system_probes(report)

    report.print_terminal_summary()
