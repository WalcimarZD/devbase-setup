"""
NuGet Support Utilities
=======================
Handles nuget.exe download and package restoration for .NET Framework projects.
"""
import subprocess
from pathlib import Path
from typing import Optional
import urllib.request
import shutil

from rich.console import Console

console = Console()

NUGET_URL = "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe"
DEVBASE_BIN_DIR = Path.home() / ".devbase" / "bin"



def get_nuget_path(root: Optional[Path] = None) -> Path:
    """
    Get path to nuget.exe, downloading if necessary.
    
    If root is provided, uses <root>/.devbase/bin/nuget.exe (Workspace-local).
    Otherwise uses ~/.devbase/bin/nuget.exe (Global).
    """
    if root:
        bin_dir = root / ".devbase" / "bin"
    else:
        bin_dir = DEVBASE_BIN_DIR
        
    nuget_path = bin_dir / "nuget.exe"
    
    if nuget_path.exists():
        return nuget_path
    
    # Download nuget.exe
    console.print(f"[dim]Downloading nuget.exe to {bin_dir}...[/dim]")
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(NUGET_URL, nuget_path)
        console.print(f"[green]✓[/green] nuget.exe saved to {nuget_path}")
    except Exception as e:
        console.print(f"[red]✗ Failed to download nuget.exe: {e}[/red]")
        raise
    
    return nuget_path


def is_dotnet_project(project_path: Path) -> bool:
    """Check if project is a .NET project (has .sln or packages.config)."""
    return any([
        list(project_path.glob("*.sln")),
        (project_path / "packages.config").exists(),
        list(project_path.glob("**/packages.config")),
    ])


def nuget_restore(project_path: Path, solution_file: Optional[str] = None, root: Optional[Path] = None) -> bool:
    """
    Run nuget restore on a project.
    
    Args:
        project_path: Path to project root
        solution_file: Optional specific .sln file to restore
        root: Workspace root for hermetic package storage
        
    Returns:
        True if successful, False otherwise
    """
    nuget_exe = get_nuget_path(root)
    
    # Configure environment for hermetic storage if root is provided
    env = None
    if root:
        import os
        env = os.environ.copy()
        
        # 1. Set global packages folder to <root>/.nuget/packages
        packages_dir = root / ".nuget" / "packages"
        env["NUGET_PACKAGES"] = str(packages_dir)
        
        # 2. Set http cache to <root>/.nuget/http-cache (prevent global pollution)
        env["NUGET_HTTP_CACHE_PATH"] = str(root / ".nuget" / "http-cache")
        
        # 3. Set plugin cache (optional but cleanliness)
        env["NUGET_PLUGINS_CACHE_PATH"] = str(root / ".nuget" / "plugins-cache")
        
        console.print(f"[dim]Using workspace NuGet cache: {packages_dir}[/dim]")
    
    # Find solution file if not specified
    if not solution_file:
        sln_files = list(project_path.glob("*.sln"))
        if not sln_files:
            console.print("[yellow]⚠ No .sln file found. Looking for packages.config...[/yellow]")
            packages_config = project_path / "packages.config"
            if packages_config.exists():
                target = str(packages_config)
            else:
                console.print("[red]✗ No solution or packages.config found.[/red]")
                return False
        else:
            target = str(sln_files[0])
            if len(sln_files) > 1:
                console.print(f"[dim]Multiple .sln files found, using: {sln_files[0].name}[/dim]")
    else:
        target = str(project_path / solution_file)
    
    console.print(f"\n[bold]Restoring NuGet packages...[/bold]")
    console.print(f"[dim]Target: {target}[/dim]\n")
    
    try:
        result = subprocess.run(
            [str(nuget_exe), "restore", target],
            cwd=str(project_path),
            env=env,  # Inject hermetic environment
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        
        if result.returncode == 0:
            console.print("[green]✓[/green] NuGet packages restored successfully")
            return True
        else:
            console.print(f"[red]✗ NuGet restore failed:[/red]\n{result.stderr or result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        console.print("[red]✗ NuGet restore timed out (5 min).[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ NuGet restore error: {e}[/red]")
        return False
