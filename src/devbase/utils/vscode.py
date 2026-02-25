"""
VS Code Workspace Utilities
===========================
Handles .code-workspace file generation for projects.
"""
import json
from pathlib import Path

from rich.console import Console

console = Console()


def generate_vscode_workspace(project_path: Path, project_name: str) -> Path:
    """
    Generate a .code-workspace file for a project.
    
    Args:
        project_path: Path to project root
        project_name: Name of the project
        
    Returns:
        Path to created workspace file
    """
    workspace_file = project_path / f"{project_name}.code-workspace"
    
    workspace_content = {
        "folders": [
            {"path": "."}
        ],
        "settings": {
            "files.exclude": {
                "**/bin": True,
                "**/obj": True,
                "**/.git": True,
                "**/node_modules": True,
                "**/__pycache__": True
            },
            "editor.formatOnSave": True
        },
        "extensions": {
            "recommendations": []
        }
    }
    
    # Detect project type and add relevant extensions
    if list(project_path.glob("*.sln")) or list(project_path.glob("*.csproj")):
        # .NET project
        workspace_content["extensions"]["recommendations"].extend([
            "ms-dotnettools.csharp",
            "ms-dotnettools.csdevkit"
        ])
    
    if list(project_path.glob("*.py")) or (project_path / "pyproject.toml").exists():
        # Python project
        workspace_content["extensions"]["recommendations"].extend([
            "ms-python.python",
            "charliermarsh.ruff"
        ])
    
    if (project_path / "package.json").exists():
        # Node.js project
        workspace_content["extensions"]["recommendations"].extend([
            "dbaeumer.vscode-eslint",
            "esbenp.prettier-vscode"
        ])
    
    workspace_file.write_text(json.dumps(workspace_content, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] Created {workspace_file.name}")
    
    return workspace_file


def open_in_vscode(path: Path) -> bool:
    """
    Open a project or file in VS Code ensuring Windows compatibility.
    
    Args:
        path: Path to project, file or workspace file
        
    Returns:
        True if successful
    """
    import subprocess
    import sys
    
    try:
        shell = sys.platform == "win32"
        subprocess.run(f'code "{path}"', shell=shell, check=False)
        return True
    except Exception as e:
        console.print(f"[red]✗ Failed to open VS Code: {e}[/red]")
        return False
