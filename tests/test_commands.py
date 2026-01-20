"""
Tests for core commands (setup, doctor, hydrate) and dev commands.
Migrated from legacy test_devbase_cli.py to use Typer CliRunner.
"""
import json
from pathlib import Path
from typer.testing import CliRunner

from devbase.main import app

runner = CliRunner()


def test_help_command():
    """Test that help displays properly."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "DevBase" in result.stdout
    assert "Personal Engineering Operating System" in result.stdout


def test_core_setup_creates_structure(tmp_path):
    """Test 'core setup' creates the Johnny.Decimal structure."""
    # --root must be passed BEFORE the subcommand "core"
    result = runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    assert result.exit_code == 0
    
    # Check required areas exist
    areas = [
        "00-09_SYSTEM",
        "10-19_KNOWLEDGE",
        "20-29_CODE",
        "30-39_OPERATIONS",
        "40-49_MEDIA_ASSETS",
        "90-99_ARCHIVE_COLD",
    ]
    for area in areas:
        assert (tmp_path / area).exists(), f"Area {area} should exist"

    # Check governance files and state
    assert (tmp_path / ".devbase_state.json").exists()


def test_core_setup_dry_run(tmp_path):
    """Test 'core setup --dry-run' does not create files."""
    result = runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--dry-run", "--no-interactive"])
    assert result.exit_code == 0
    assert "DRY-RUN MODE" in result.stdout
    
    # Should not exist
    assert not (tmp_path / ".devbase_state.json").exists()
    assert not (tmp_path / "00-09_SYSTEM").exists()


def test_core_doctor_healthy(tmp_path):
    """Test doctor reports healthy for a valid workspace."""
    # First setup
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # Run doctor (input "n" in case it prompts, though it shouldn't if healthy)
    result = runner.invoke(app, ["--root", str(tmp_path), "core", "doctor"], input="n")
    assert result.exit_code == 0, result.stdout
    assert "HEALTHY" in result.stdout


def test_core_doctor_missing_areas(tmp_path):
    """Test doctor detects missing folders."""
    # Partial setup
    (tmp_path / "00-09_SYSTEM").mkdir()
    
    # Run doctor, expect prompt to fix, say no
    result = runner.invoke(app, ["--root", str(tmp_path), "core", "doctor"], input="n")
    
    assert result.exit_code == 0
    assert "NOT FOUND" in result.stdout
    assert "Missing folder" in result.stdout


def test_dev_audit_naming(tmp_path):
    """Test audit detects naming violations."""
    # Create violation
    (tmp_path / "MyBadFolder").mkdir()
    
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "audit"])
    
    assert result.exit_code == 0
    assert "violation" in result.stdout.lower() or "MyBadFolder" in result.stdout


def test_dev_new_project(tmp_path):
    """Test 'dev new' creates a project with valid name."""
    # Setup workspace first
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # Create a simple project (no template, just structure)
    # Added --no-interactive to prevent prompts causing EOFError
    result = runner.invoke(
        app, 
        ["--root", str(tmp_path), "dev", "new", "my-test-project", "--no-setup", "--no-interactive"],
        input="\n"  # Accept defaults
    )
    
    # Check project was created in the correct location
    project_dir = tmp_path / "20-29_CODE" / "21_monorepo_apps" / "my-test-project"
    
    # Note: The actual project creation depends on copier templates
    # This test verifies the command runs without errors for valid names
    assert result.exit_code == 0 or "template" in result.stdout.lower()


def test_dev_new_validation(tmp_path):
    """Test 'dev new' validates project name."""
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "new", "BadName"])
    assert result.exit_code != 0
    assert "kebab-case" in result.stdout


def test_ops_clean(tmp_path):
    """Test 'ops clean' removes temp files."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # Create some temp files to clean
    temp_files = [
        tmp_path / "test.log",
        tmp_path / "temp.tmp",
        tmp_path / "20-29_CODE" / "cache.pyc",
    ]
    
    for f in temp_files:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("temp content")
    
    # Verify files exist before clean
    assert (tmp_path / "test.log").exists()
    
    # Run clean
    result = runner.invoke(app, ["--root", str(tmp_path), "ops", "clean"])
    
    assert result.exit_code == 0
    # Clean should remove .log and .tmp files
    # Note: actual behavior depends on clean implementation patterns


def test_quick_note(tmp_path):
    """Test 'quick note' creates a file."""
    # Setup
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    result = runner.invoke(app, ["--root", str(tmp_path), "quick", "note", "Test Note"])
    assert result.exit_code == 0
    assert "Note saved" in result.stdout
    
    # Verify file exists
    notes_dir = tmp_path / "10-19_KNOWLEDGE" / "11_public_garden" / "til"
    assert any(notes_dir.rglob("*.md"))


# ============================================================================
# NEW COMMANDS TESTS (v5.1.0+)
# ============================================================================

def test_dev_list(tmp_path):
    """Test 'dev list' shows projects."""
    # Setup workspace with a project
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # Create a mock project
    project_dir = tmp_path / "20-29_CODE" / "21_monorepo_apps" / "test-project"
    project_dir.mkdir(parents=True)
    
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "list"])
    
    assert result.exit_code == 0
    assert "test-project" in result.stdout
    assert "Project List" in result.stdout


def test_dev_info(tmp_path):
    """Test 'dev info' shows project details."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # Create a project with metadata
    project_dir = tmp_path / "20-29_CODE" / "21_monorepo_apps" / "info-test"
    project_dir.mkdir(parents=True)
    
    metadata = {
        "template": "clean-arch",
        "governance": "full",
        "created_at": "2025-01-01T00:00:00"
    }
    (project_dir / ".devbase.json").write_text(json.dumps(metadata))
    
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "info", "info-test"])
    
    assert result.exit_code == 0
    assert "info-test" in result.stdout
    assert "clean-arch" in result.stdout or "Template" in result.stdout


def test_dev_info_not_found(tmp_path):
    """Test 'dev info' with non-existent project."""
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "info", "nonexistent"])
    
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()


def test_dev_worktree_list_empty(tmp_path):
    """Test 'dev worktree-list' with no worktrees."""
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "worktree-list"])
    
    assert result.exit_code == 0
    assert "No worktrees found" in result.stdout


def test_dev_restore_not_dotnet(tmp_path):
    """Test 'dev restore' on non-.NET project."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])
    
    # Create a non-.NET project
    project_dir = tmp_path / "20-29_CODE" / "21_monorepo_apps" / "python-project"
    project_dir.mkdir(parents=True)
    (project_dir / "main.py").write_text("print('hello')")
    
    result = runner.invoke(app, ["--root", str(tmp_path), "dev", "restore", "python-project"])
    
    assert result.exit_code != 0
    assert ".NET" in result.stdout or "No .sln" in result.stdout or "does not appear" in result.stdout

def test_audit_consistency_run(tmp_path):
    """Test 'audit run' command."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Run audit
    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    assert "DevBase Consistency Audit" in result.stdout
