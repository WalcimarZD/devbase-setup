"""
Project Setup Service
=====================
Encapsulates "Golden Path" logic for bootstrapping new projects.

Uses a Strategy Pattern for dependency installation so each ecosystem
(Python, Node, Go, Rust) has a single focused installer with one reason
to change (OCP + SRP).
"""
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

console = Console()


# ---------------------------------------------------------------------------
# Installer Strategies
# ---------------------------------------------------------------------------

class InstallerStrategy(ABC):
    """Abstract strategy for polyglot dependency installation."""

    @abstractmethod
    def can_install(self, path: Path) -> bool:
        """Return True if this strategy applies to the project at *path*."""
        ...

    @abstractmethod
    def install(self, path: Path) -> None:
        """Install dependencies for the project at *path*."""
        ...


class PythonInstaller(InstallerStrategy):
    """Install Python dependencies using uv."""

    def can_install(self, path: Path) -> bool:
        return (path / "pyproject.toml").exists() and bool(shutil.which("uv"))

    def install(self, path: Path) -> None:
        subprocess.run(["uv", "sync"], cwd=path, check=True, capture_output=True)


class NodeInstaller(InstallerStrategy):
    """Install Node.js dependencies using npm."""

    def can_install(self, path: Path) -> bool:
        return (path / "package.json").exists() and bool(shutil.which("npm"))

    def install(self, path: Path) -> None:
        subprocess.run(["npm", "install"], cwd=path, check=True, capture_output=True)


class GoInstaller(InstallerStrategy):
    """Download Go modules."""

    def can_install(self, path: Path) -> bool:
        return (path / "go.mod").exists() and bool(shutil.which("go"))

    def install(self, path: Path) -> None:
        subprocess.run(["go", "mod", "download"], cwd=path, check=True, capture_output=True)


class RustInstaller(InstallerStrategy):
    """Fetch Rust dependencies using cargo."""

    def can_install(self, path: Path) -> bool:
        return (path / "Cargo.toml").exists() and bool(shutil.which("cargo"))

    def install(self, path: Path) -> None:
        subprocess.run(["cargo", "fetch"], cwd=path, check=True, capture_output=True)


_INSTALLERS: list[InstallerStrategy] = [
    PythonInstaller(),
    NodeInstaller(),
    GoInstaller(),
    RustInstaller(),
]


# ---------------------------------------------------------------------------
# Main Service
# ---------------------------------------------------------------------------

class ProjectSetupService:
    """\"Golden Path\" bootstrapper for new projects.

    Args:
        root: Workspace root (reserved for future workspace-aware logic).
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def run_golden_path(
        self,
        project_path: Path,
        project_name: str,
        interactive: bool = True,
    ) -> bool:
        """Run the full Golden Path setup sequence.

        Steps: git init → dependencies → pre-commit → initial commit → IDE.

        Args:
            project_path: Directory of the newly scaffolded project.
            project_name: Human-readable project name.
            interactive: If ``True``, prompt before running install commands.

        Returns:
            ``True`` on success.
        """
        console.print(f"\n[bold cyan]\U0001f680 Bootstrapping '{project_name}'...[/bold cyan]")
        self._git_init(project_path)
        self._install_dependencies(project_path, interactive=interactive)
        self._setup_pre_commit(project_path)
        self._initial_commit(project_path, project_name)
        self._open_ide(project_path)
        return True

    def _git_init(self, path: Path) -> None:
        try:
            with console.status("[bold cyan]Initializing Git...[/bold cyan]"):
                subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
            console.print("  [green]\u2713[/green] Git initialized")
        except Exception:
            console.print("  [yellow]\u26a0[/yellow] Git init failed")

    def _install_dependencies(self, path: Path, interactive: bool = True) -> None:
        """Detect the project ecosystem and run the appropriate installer."""

        def confirm(label: str) -> bool:
            return Confirm.ask(f"Run [bold cyan]{label}[/bold cyan]?", default=True) if interactive else True

        for installer in _INSTALLERS:
            if not installer.can_install(path):
                continue

            label = type(installer).__name__.replace("Installer", "")
            if not confirm(label):
                console.print(f"  [dim]Skipped {label} install[/dim]")
                return

            try:
                with console.status(f"[bold cyan]Installing {label} dependencies...[/bold cyan]"):
                    installer.install(path)
                console.print(f"  [green]\u2713[/green] {label} deps installed")
            except subprocess.CalledProcessError:
                console.print(f"  [red]\u2717[/red] {label} install failed")
            return

        console.print("  [dim]No dependency file found (generic project)[/dim]")

    def _setup_pre_commit(self, path: Path) -> None:
        if (path / ".pre-commit-config.yaml").exists() and shutil.which("pre-commit"):
            try:
                with console.status("[bold cyan]Setting up pre-commit...[/bold cyan]"):
                    subprocess.run(["pre-commit", "install"], cwd=path, check=True, capture_output=True)
                console.print("  [green]\u2713[/green] Hooks installed")
            except Exception:
                console.print("  [yellow]\u26a0[/yellow] pre-commit failed")

    def _initial_commit(self, path: Path, project_name: str) -> None:
        try:
            with console.status("[bold cyan]Creating initial commit...[/bold cyan]"):
                subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
                subprocess.run(
                    ["git", "commit", "-m", f"feat: Initialize {project_name}"],
                    cwd=path, check=True, capture_output=True,
                )
            console.print("  [green]\u2713[/green] Initial commit created")
        except Exception:
            console.print("  [yellow]\u26a0[/yellow] Commit failed")

    def _open_ide(self, path: Path) -> None:
        if shutil.which("code"):
            console.print("[dim]\u26a1 Opening VS Code...[/dim]")
            subprocess.run(["code", str(path)], check=False)
            console.print("  [green]\u2713[/green] Done")


def get_project_setup(root: Path) -> ProjectSetupService:
    return ProjectSetupService(root)

