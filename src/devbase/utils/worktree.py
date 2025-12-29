"""
Git Worktree Utilities
======================
Handles git worktree creation, listing, and management.
"""
import subprocess
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from rich.console import Console

console = Console()


def sanitize_branch_name(branch: str) -> str:
    """Convert branch name to safe directory name."""
    return branch.replace("/", "--").replace("\\", "--")


def get_worktree_dir(root: Path) -> Path:
    """Get the worktrees directory."""
    return root / "20-29_CODE" / "22_worktrees"


def list_worktrees(project_path: Path) -> List[dict]:
    """
    List all worktrees for a git repository.
    
    Returns:
        List of dicts with worktree info (path, branch, commit)
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        worktrees = []
        current = {}
        
        for line in result.stdout.strip().split("\n"):
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line[9:]}
            elif line.startswith("HEAD "):
                current["commit"] = line[5:][:8]
            elif line.startswith("branch "):
                current["branch"] = line[7:].replace("refs/heads/", "")
            elif line == "detached":
                current["branch"] = "(detached)"
        
        if current:
            worktrees.append(current)
            
        return worktrees
        
    except Exception:
        return []


def add_worktree(
    project_path: Path,
    worktrees_dir: Path,
    project_name: str,
    branch: str,
    create_branch: bool = False
) -> Optional[Path]:
    """
    Add a new worktree for a project.
    
    Args:
        project_path: Path to main project
        worktrees_dir: Directory to create worktree in
        project_name: Name of the project
        branch: Branch name
        create_branch: If True, create a new branch
        
    Returns:
        Path to created worktree, or None on failure
    """
    worktree_name = f"{project_name}--{sanitize_branch_name(branch)}"
    worktree_path = worktrees_dir / worktree_name
    
    if worktree_path.exists():
        console.print(f"[yellow]⚠ Worktree already exists: {worktree_name}[/yellow]")
        return None
    
    worktrees_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = ["git", "worktree", "add"]
    if create_branch:
        cmd.extend(["-b", branch])
    cmd.extend([str(worktree_path), branch])
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            console.print(f"[red]✗ Failed to create worktree:[/red]\n{result.stderr}")
            return None
        
        console.print(f"[green]✓[/green] Created worktree: {worktree_name}")
        
        # Create .devbase.json for the worktree
        import devbase
        metadata = {
            "template": "worktree",
            "governance": "external",
            "parent_project": project_name,
            "branch": branch,
            "created_at": datetime.now().isoformat(),
            "devbase_version": devbase.__version__
        }
        (worktree_path / ".devbase.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )
        
        return worktree_path
        
    except subprocess.TimeoutExpired:
        console.print("[red]✗ Worktree creation timed out.[/red]")
        return None
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return None


def remove_worktree(project_path: Path, worktree_path: Path, force: bool = False) -> bool:
    """
    Remove a worktree.
    
    Args:
        project_path: Path to main project
        worktree_path: Path to worktree to remove
        force: Force removal even with uncommitted changes
        
    Returns:
        True if successful
    """
    cmd = ["git", "worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(worktree_path))
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            console.print(f"[red]✗ Failed to remove worktree:[/red]\n{result.stderr}")
            return False
        
        console.print(f"[green]✓[/green] Removed worktree: {worktree_path.name}")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        return False


def get_stale_worktrees(project_path: Path) -> List[Path]:
    """
    Find worktrees with deleted branches.
    
    Returns:
        List of paths to stale worktrees
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        stale = []
        current_path = None
        is_stale = False
        
        for line in result.stdout.strip().split("\n"):
            if line.startswith("worktree "):
                if current_path and is_stale:
                    stale.append(Path(current_path))
                current_path = line[9:]
                is_stale = False
            elif line == "prunable":
                is_stale = True
        
        if current_path and is_stale:
            stale.append(Path(current_path))
            
        return stale
        
    except Exception:
        return []
