"""
Project Setup Service
=====================
Encapsulates "Golden Path" logic for bootstrapping new projects.
Supports Polyglot setups (Python, Node.js, Generic).
"""
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

console = Console()

class ProjectSetupService:
    def __init__(self, root: Path):
        self.root = root

    def run_golden_path(self, project_path: Path, project_name: str, interactive: bool = True) -> bool:
        """
        Run the full "Golden Path" setup for a generated project.
        
        Steps:
        1. Git Init
        2. Dependency Install (Polyglot)
        3. Pre-commit
        4. Initial Commit
        5. Setup IDE
        """
        console.print(f"\n[bold cyan]🚀 Bootstrapping '{project_name}'...[/bold cyan]")

        # 1. Git Init
        self._git_init(project_path)
        
        # 2. Dependencies
        self._install_dependencies(project_path, interactive=interactive)
        
        # 3. Pre-commit
        self._setup_pre_commit(project_path)
        
        # 4. Initial Commit
        self._initial_commit(project_path, project_name)
        
        # 5. Open IDE
        self._open_ide(project_path)
        
        return True

    def _git_init(self, path: Path):
        try:
            with console.status("[bold cyan]Initializing Git...[/bold cyan]"):
                subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
            console.print("  [green]✓[/green] Git initialized")
        except Exception:
            console.print("  [yellow]⚠[/yellow] Git init failed")

    def _install_dependencies(self, path: Path, interactive: bool = True):
        """
        Polyglot dependency installation.

        Security: Asks for confirmation before running install scripts unless not interactive.
        """
        
        # Helper to confirm execution
        def confirm_exec(command_desc: str) -> bool:
            if not interactive:
                return True
            return Confirm.ask(f"Run [bold cyan]{command_desc}[/bold cyan]?", default=True)

        # Python (uv) - Priority
        if (path / "pyproject.toml").exists():
            if shutil.which("uv"):
                if confirm_exec("uv sync"):
                    try:
                        with console.status("[bold cyan]Installing Python dependencies (uv)...[/bold cyan]"):
                            subprocess.run(["uv", "sync"], cwd=path, check=True, capture_output=True)
                        console.print("  [green]✓[/green] Python deps (uv)")
                        return
                    except subprocess.CalledProcessError:
                        console.print("  [red]✗[/red] uv sync failed")
                else:
                     console.print("  [dim]Skipped uv sync[/dim]")
            else:
                console.print("  [yellow]⚠[/yellow] uv not found")
        
        # Node.js (npm)
        elif (path / "package.json").exists():
            if shutil.which("npm"):
                if confirm_exec("npm install"):
                    try:
                        with console.status("[bold cyan]Installing Node dependencies (npm)...[/bold cyan]"):
                            subprocess.run(["npm", "install"], cwd=path, check=True, capture_output=True)
                        console.print("  [green]✓[/green] Node deps (npm)")
                        return
                    except subprocess.CalledProcessError:
                        console.print("  [red]✗[/red] npm install failed")
                else:
                    console.print("  [dim]Skipped npm install[/dim]")
            else:
                console.print("  [yellow]⚠[/yellow] npm not found")
        
        else:
            # Go (go.mod)
            if (path / "go.mod").exists():
                if shutil.which("go"):
                    if confirm_exec("go mod download"):
                        try:
                            with console.status("[bold cyan]Downloading Go modules...[/bold cyan]"):
                                subprocess.run(["go", "mod", "download"], cwd=path, check=True, capture_output=True)
                            console.print("  [green]✓[/green] Go deps (go mod)")
                            return
                        except subprocess.CalledProcessError:
                            console.print("  [red]✗[/red] go mod download failed")
                    else:
                        console.print("  [dim]Skipped go mod download[/dim]")
                else:
                    console.print("  [yellow]⚠[/yellow] go not found")

            # Rust (Cargo.toml)
            elif (path / "Cargo.toml").exists():
                if shutil.which("cargo"):
                    if confirm_exec("cargo fetch"):
                        try:
                            # minimal check, build usually fetches deps
                            with console.status("[bold cyan]Fetching Rust dependencies...[/bold cyan]"):
                                subprocess.run(["cargo", "fetch"], cwd=path, check=True, capture_output=True)
                            console.print("  [green]✓[/green] Rust deps (cargo)")
                            return
                        except subprocess.CalledProcessError:
                            console.print("  [red]✗[/red] cargo fetch failed")
                    else:
                        console.print("  [dim]Skipped cargo fetch[/dim]")
                else:
                    console.print("  [yellow]⚠[/yellow] cargo not found")
            
            else:
                console.print("  [dim]No dependency file found (generic project)[/dim]")

    def _setup_pre_commit(self, path: Path):
        if (path / ".pre-commit-config.yaml").exists() and shutil.which("pre-commit"):
            try:
                with console.status("[bold cyan]Setting up pre-commit...[/bold cyan]"):
                    subprocess.run(["pre-commit", "install"], cwd=path, check=True, capture_output=True)
                console.print("  [green]✓[/green] Hooks installed")
            except Exception:
                console.print("  [yellow]⚠[/yellow] pre-commit failed")

    def _initial_commit(self, path: Path, project_name: str):
        try:
            with console.status("[bold cyan]Creating initial commit...[/bold cyan]"):
                subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", f"feat: Initialize {project_name}"], cwd=path, check=True, capture_output=True)
            console.print("  [green]✓[/green] Initial commit created")
        except Exception:
            console.print("  [yellow]⚠[/yellow] Commit failed")

    def _open_ide(self, path: Path):
        if shutil.which("code"):
            console.print("[dim]⚡ Opening VS Code...[/dim]")
            subprocess.run(["code", "--", str(path)], check=False)
            console.print("  [green]✓[/green] Done")

def get_project_setup(root: Path) -> ProjectSetupService:
    return ProjectSetupService(root)
