import pytest
import os
from pathlib import Path
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

@pytest.fixture
def mock_workspace(tmp_path):
    """Setup a valid DevBase workspace in tmp_path."""
    (tmp_path / ".devbase_state.json").write_text("{}")

    (tmp_path / "src/devbase/commands").mkdir(parents=True)
    (tmp_path / "src/devbase/services").mkdir(parents=True)
    (tmp_path / "docs/cli").mkdir(parents=True)

    # Defaults
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies=[]')
    (tmp_path / "ARCHITECTURE.md").write_text("")
    (tmp_path / "README.md").write_text("")
    (tmp_path / "USAGE-GUIDE.md").write_text("")
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").write_text("hot_fts cold_fts")
    (tmp_path / "src/devbase/services/knowledge_db.py").write_text("hot_fts cold_fts")
    (tmp_path / "CHANGELOG.md").write_text("## [Unreleased]")

    return tmp_path

def test_audit_no_issues(mock_workspace):
    """Test audit passes when everything is consistent."""

    # Mock CLI command
    (mock_workspace / "src/devbase/commands/core.py").write_text("""
import typer
app = typer.Typer()
@app.command("test")
def test_cmd():
    pass
""")

    # Mock USAGE-GUIDE.md
    (mock_workspace / "USAGE-GUIDE.md").write_text("Run `devbase core test`.")

    cwd = os.getcwd()
    os.chdir(mock_workspace)
    try:
        # Pass --root explicitly to be sure, though cwd helps
        result = runner.invoke(app, ["--root", str(mock_workspace), "audit", "run"])
        assert result.exit_code == 0
        assert "System is consistent" in result.stdout
    finally:
        os.chdir(cwd)

def test_audit_detects_undocumented_flag(mock_workspace):
    """Test audit detects a new flag in a command."""

    # Command with a flag
    (mock_workspace / "src/devbase/commands/core.py").write_text("""
import typer
app = typer.Typer()
@app.command("test")
def test_cmd(flag: bool = typer.Option(False, "--new-flag")):
    pass
""")

    # Docs mention command but NOT flag
    (mock_workspace / "USAGE-GUIDE.md").write_text("Run `devbase core test`.")

    cwd = os.getcwd()
    os.chdir(mock_workspace)
    try:
        result = runner.invoke(app, ["--root", str(mock_workspace), "audit", "run"])
        assert result.exit_code == 0
        assert "Undocumented CLI items" in result.stdout
        assert "--new-flag" in result.stdout
    finally:
        os.chdir(cwd)

def test_audit_detects_missing_db_docs(mock_workspace):
    """Test audit detects missing hot_fts/cold_fts in docs."""

    # DB has tables
    (mock_workspace / "src/devbase/services/knowledge_db.py").write_text("""
CREATE TABLE hot_fts (id text);
CREATE TABLE cold_fts (id text);
""")

    # Docs missing them
    (mock_workspace / "docs/TECHNICAL_DESIGN_DOC.md").write_text("Documentation.")

    cwd = os.getcwd()
    os.chdir(mock_workspace)
    try:
        result = runner.invoke(app, ["--root", str(mock_workspace), "audit", "run"])
        assert result.exit_code == 0
        assert "Tables missing in TECHNICAL_DESIGN_DOC.md" in result.stdout
        assert "hot_fts" in result.stdout
    finally:
        os.chdir(cwd)

def test_audit_detects_changelog_issue(mock_workspace):
    """Test audit warns about Changelog structure."""

    (mock_workspace / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0.0\n")

    # Trigger a change by creating a new file (audit checks for changes)
    (mock_workspace / "src/devbase/new_file.py").touch()

    cwd = os.getcwd()
    os.chdir(mock_workspace)
    try:
        result = runner.invoke(app, ["--root", str(mock_workspace), "audit", "run"])
        assert result.exit_code == 0
        assert "Checking Changelog" in result.stdout
        assert "missing 'In Progress' or 'Unreleased' section" in result.stdout

        # Test FIX
        result_fix = runner.invoke(app, ["--root", str(mock_workspace), "audit", "run", "--fix"])
        assert result_fix.exit_code == 0
        assert "added In Progress section" in result_fix.stdout

        content = (mock_workspace / "CHANGELOG.md").read_text()
        assert "## [Unreleased] - In Progress" in content
    finally:
        os.chdir(cwd)

def test_audit_detects_undocumented_dependency(mock_workspace):
    """Test audit detects a dependency in pyproject.toml missing from docs."""

    # Add a new dependency
    (mock_workspace / "pyproject.toml").write_text("""
[project]
dependencies = ["new-lib"]
""")

    # Docs are empty (from fixture default)

    cwd = os.getcwd()
    os.chdir(mock_workspace)
    try:
        result = runner.invoke(app, ["--root", str(mock_workspace), "audit", "run"])
        assert result.exit_code == 0
        # It should warn about new-lib missing in ARCHITECTURE.md and README.md
        assert "Dependencies missing in ARCHITECTURE.md" in result.stdout
        assert "new-lib" in result.stdout
        assert "Dependencies missing in README.md" in result.stdout
    finally:
        os.chdir(cwd)
