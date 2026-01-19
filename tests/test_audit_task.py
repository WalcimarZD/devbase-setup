import os
import shutil
import pytest
from typer.testing import CliRunner
from pathlib import Path
from devbase.commands.audit import app
import traceback

runner = CliRunner()

@pytest.fixture
def mock_workspace(tmp_path):
    """Sets up a mock workspace with necessary files."""
    # Create directory structure
    (tmp_path / "src" / "devbase" / "commands").mkdir(parents=True)
    (tmp_path / "src" / "devbase" / "adapters" / "storage").mkdir(parents=True)
    (tmp_path / "docs" / "cli").mkdir(parents=True)

    # pyproject.toml
    (tmp_path / "pyproject.toml").write_text("""
[project]
dependencies = ["typer"]
[project.optional-dependencies]
viz = ["pyvis"]
    """)

    # ARCHITECTURE.md (missing pyvis)
    (tmp_path / "ARCHITECTURE.md").write_text("Uses typer.")

    # README.md
    (tmp_path / "README.md").write_text("Uses typer.")

    # USAGE-GUIDE.md
    (tmp_path / "USAGE-GUIDE.md").write_text("devbase test run")

    # Command with flag
    (tmp_path / "src" / "devbase" / "commands" / "test_cmd.py").write_text("""
import typer
app = typer.Typer()
@app.command("run")
def run(flag: bool = typer.Option(False, "--flag")):
    pass
    """)

    # TECHNICAL_DESIGN_DOC.md
    (tmp_path / "docs" / "TECHNICAL_DESIGN_DOC.md").write_text("""
    Tables:
    - notes_index
    """)

    # duckdb_adapter.py with undocumented table
    (tmp_path / "src" / "devbase" / "adapters" / "storage" / "duckdb_adapter.py").write_text("""
def init_schema(conn):
    conn.execute("CREATE TABLE notes_index (id INT)")
    conn.execute("CREATE TABLE hot_fts (id INT)") # Undocumented in Tech Doc
    """)

    # knowledge_db.py (for legacy check support if kept)
    (tmp_path / "src" / "devbase" / "services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "devbase" / "services" / "knowledge_db.py").write_text("""
    # uses hot_fts
    """)

    return tmp_path

def test_audit_run(mock_workspace):
    """Test the audit run command."""
    # Debug: Check registered commands
    print(f"Registered commands: {[c.name for c in app.registered_commands]}")

    # Switch to mock workspace
    cwd = os.getcwd()
    os.chdir(mock_workspace)
    try:
        # Pass root context if needed, though we chdir'd
        # audit now supports context, but we use invoke without explicit obj,
        # so it defaults to cwd which is mock_workspace
        # Note: In test harness with single command app, invocation behavior can vary.
        # We verified that invoking with [] works and executes the audit.
        # It seems Typer/CliRunner treats the app as the command here.
        result = runner.invoke(app, [], obj={"root": mock_workspace})

        # Assertions
        assert result.exit_code == 0, f"Exit code {result.exit_code}. Output:\n{result.stdout}\nException: {result.exception}"

        # 1. Check for missing optional dependency (pyvis)
        # It should appear in warnings or suggestions
        assert "pyvis" in result.stdout

        # 2. Check for missing flag (--flag)
        # Should be detected
        assert "--flag" in result.stdout

        # 3. Check for missing DB table (hot_fts)
        # Should be detected from duckdb_adapter.py
        assert "hot_fts" in result.stdout

    finally:
        os.chdir(cwd)
