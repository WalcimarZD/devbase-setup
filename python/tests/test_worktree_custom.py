import os
import shutil
import subprocess
from pathlib import Path
from typer.testing import CliRunner
import pytest
from devbase.main import app

runner = CliRunner()

@pytest.fixture
def workspace_with_git(tmp_path):
    """
    Creates a workspace with a git project initialized.
    """
    # 1. Setup devbase structure
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # 2. Create a project manually to ensure it has git
    project_name = "test-project"
    project_dir = tmp_path / "20-29_CODE" / "21_monorepo_apps" / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Init git
    subprocess.run(["git", "init"], cwd=str(project_dir), check=True)
    
    # Configure git for dummy commits
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(project_dir), check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(project_dir), check=True)
    
    # Create a file and commit
    (project_dir / "README.md").write_text("# Test Project")
    subprocess.run(["git", "add", "README.md"], cwd=str(project_dir), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(project_dir), check=True)
    
    # Create a develop branch to serve as base for worktrees
    subprocess.run(["git", "checkout", "-b", "develop"], cwd=str(project_dir), check=True)
    
    return tmp_path, project_name

def test_worktree_add_default_name(workspace_with_git):
    """Test creating a worktree with default naming convention."""
    root, project_name = workspace_with_git
    branch_name = "feature/default-naming"
    
    # Create worktree
    result = runner.invoke(app, [
        "--root", str(root), 
        "dev", "worktree-add", 
        project_name, 
        branch_name, 
        "--create"
    ])
    
    assert result.exit_code == 0
    assert "Created worktree" in result.stdout
    
    # Check folder name (sanitized) WITH SINGLE DASH
    expected_folder = f"{project_name}-feature--default-naming"
    worktree_path = root / "20-29_CODE" / "22_worktrees" / expected_folder
    
    assert worktree_path.exists()
    assert (worktree_path / ".git").exists()
    assert (worktree_path / ".devbase.json").exists()

def test_worktree_add_custom_name(workspace_with_git):
    """Test creating a worktree with a custom name."""
    root, project_name = workspace_with_git
    branch_name = "feature/custom-naming"
    custom_name = "my-custom-worktree"
    
    # Create worktree with --name
    result = runner.invoke(app, [
        "--root", str(root), 
        "dev", "worktree-add", 
        project_name, 
        branch_name, 
        "--create",
        "--name", custom_name
    ])
    
    assert result.exit_code == 0
    assert custom_name in result.stdout
    
    # Check folder name
    worktree_path = root / "20-29_CODE" / "22_worktrees" / custom_name
    
    assert worktree_path.exists()
    assert (worktree_path / ".git").exists()
    
    # Check .devbase.json has parent_project
    import json
    meta_path = worktree_path / ".devbase.json"
    assert meta_path.exists()
    
    meta = json.loads(meta_path.read_text())
    assert meta["parent_project"] == project_name
    assert meta["branch"] == branch_name
    assert meta["template"] == "worktree"


def test_worktree_remove_custom_name(workspace_with_git):
    """Test removing a worktree with a custom name."""
    root, project_name = workspace_with_git
    branch_name = "feature/to-remove"
    custom_name = "cleanup-target"
    
    # 1. Create it first
    runner.invoke(app, [
        "--root", str(root), 
        "dev", "worktree-add", 
        project_name, 
        branch_name, 
        "--create",
        "--name", custom_name
    ])
    
    worktree_path = root / "20-29_CODE" / "22_worktrees" / custom_name
    assert worktree_path.exists()
    
    # 2. Remove it
    result = runner.invoke(app, [
        "--root", str(root), 
        "dev", "worktree-remove", 
        custom_name,
        "--force" # Force because we didn't commit anything there etc
    ])
    
    assert result.exit_code == 0
    assert "Removed worktree" in result.stdout
    
    # 3. Verify it's gone
    assert not worktree_path.exists()
    
    # 4. Verify git worktree list is clean (via subprocess check on the main repo)
    project_dir = root / "20-29_CODE" / "21_monorepo_apps" / project_name
    proc = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], 
        cwd=str(project_dir), 
        capture_output=True, 
        text=True
    )
    assert custom_name not in proc.stdout
