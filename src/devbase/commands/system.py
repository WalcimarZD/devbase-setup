"""
System Commands: self-update, maintenance
==========================================
Commands for managing the DevBase tool itself.
"""
import os
import subprocess as sp
import re
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="System maintenance and updates")
console = Console()

@app.command(name="self-update")
def self_update() -> None:
    """
    🔄 [bold]Update DevBase to the latest version.[/bold]

    Detects the installation source (local or remote) and performs 
    an atomic upgrade using the 'uv' infrastructure.
    """
    console.print("[bold]Checking for updates...[/bold]")
    
    custom_env = os.environ.copy()
    custom_env["UV_PYTHON_PREFERENCE"] = "only-managed"

    try:
        # 1. Discover installation source
        list_result = sp.run(["uv", "tool", "list"], capture_output=True, text=True, env=custom_env)
        match = re.search(r"devbase .* \(from (file:///|)(.*)\)", list_result.stdout)
        
        source_path = None
        if match:
            source_path = match.group(2).strip()
            if source_path.startswith("/") and source_path[2] == ":":
                source_path = source_path[1:]
            console.print(f"[dim]Installation source detected: {source_path}[/dim]")

        # 2. Try Standard Upgrade
        result = sp.run(["uv", "tool", "upgrade", "devbase"], capture_output=True, text=True, env=custom_env)
        
        if result.returncode == 0:
            console.print("[green]✓[/green] DevBase updated via standard upgrade.")
            return

        # 3. Fallback to Source-based Reinstall
        if source_path and Path(source_path).exists():
            console.print(f"[dim]Standard upgrade failed. Re-installing from source...[/dim]")
            result = sp.run(
                ["uv", "tool", "install", ".", "--force", "--reinstall", "--with", ".[all]"],
                cwd=source_path,
                capture_output=True,
                text=True,
                env=custom_env
            )
            
            if result.returncode == 0:
                console.print("[green]✓[/green] DevBase updated successfully from source.")
            else:
                console.print(f"[red]✗[/red] Update failed: {result.stderr.strip()}")
        else:
            console.print(f"[red]✗[/red] Standard upgrade failed and source path not found.")
    except Exception as e:
        console.print(f"[red]✗[/red] Update process error: {e}")
