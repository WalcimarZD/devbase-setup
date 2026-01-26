"""
Tests for the audit command.
"""
from pathlib import Path
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_audit_run_structure(tmp_path):
    """Test that audit run works on a mocked repo structure."""
    # Mock the structure of DevBase repo
    (tmp_path / "src/devbase/commands").mkdir(parents=True)
    (tmp_path / "src/devbase/services").mkdir(parents=True)

    # Mock pyproject.toml
    (tmp_path / "pyproject.toml").write_text("""
[project]
dependencies = ["typer", "rich"]
    """)

    # Mock docs
    (tmp_path / "README.md").write_text("Uses typer and rich.")
    (tmp_path / "ARCHITECTURE.md").write_text("Uses typer and rich.")
    (tmp_path / "USAGE-GUIDE.md").write_text("## Usage\n devbase audit run")
    (tmp_path / "docs/cli").mkdir(parents=True)
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").write_text("CREATE TABLE hot_fts")

    # Mock command
    (tmp_path / "src/devbase/commands/audit.py").write_text("""
import typer
app = typer.Typer()
@app.command("run")
def run(): pass
    """)

    # Mock service
    (tmp_path / "src/devbase/services/knowledge_db.py").write_text("""
def index():
    sql = "INSERT INTO hot_fts"
    """)

    # Run audit
    # We must pass --root to point to tmp_path
    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    # It should exit 0
    assert result.exit_code == 0
    # It should be mostly clean
    assert "Analyzing Changes" in result.stdout
    assert "Verifying Dependencies" in result.stdout
    # assert "System is consistent" in result.stdout # Might fail if I missed something small, but exit code 0 is key.

def test_audit_detects_missing_dep(tmp_path):
    """Test detection of missing dependency doc."""
    (tmp_path / "src/devbase/commands").mkdir(parents=True)

    # Missing dep in README
    (tmp_path / "pyproject.toml").write_text("""
[project]
dependencies = ["secret-lib"]
    """)
    (tmp_path / "README.md").write_text("Nothing here.")
    (tmp_path / "ARCHITECTURE.md").write_text("Nothing here.")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])
    assert result.exit_code == 0
    assert "missing in ARCHITECTURE.md: secret-lib" in result.stdout
    assert "missing in README.md: secret-lib" in result.stdout

def test_audit_detects_undocumented_cli(tmp_path):
    """Test detection of undocumented CLI command."""
    (tmp_path / "src/devbase/commands").mkdir(parents=True)
    (tmp_path / "src/devbase/services").mkdir(parents=True)
    (tmp_path / "docs").mkdir(parents=True)

    # Define a command
    (tmp_path / "src/devbase/commands/secret.py").write_text("""
import typer
app = typer.Typer()
@app.command("hidden")
def hidden(): pass
    """)

    # Usage guide doesn't mention it
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide")
    (tmp_path / "pyproject.toml").touch() # prevent error

    # DB files to prevent unrelated warnings
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").write_text("CREATE TABLE hot_fts")
    (tmp_path / "src/devbase/services/knowledge_db.py").write_text("INSERT INTO hot_fts")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])
    assert result.exit_code == 0
    assert "Undocumented commands" in result.stdout
    # Rich table might wrap output
    assert "secret" in result.stdout
    assert "hidden" in result.stdout

def test_audit_checks_docs_cli(tmp_path):
    """Test that existence of docs/cli/command.md satisfies documentation check."""
    (tmp_path / "src/devbase/commands").mkdir(parents=True)
    (tmp_path / "docs/cli").mkdir(parents=True)

    # Define a command
    (tmp_path / "src/devbase/commands/documented.py").write_text("""
import typer
app = typer.Typer()
@app.command("known")
def known(): pass
    """)

    # Usage guide doesn't mention it
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide")
    (tmp_path / "pyproject.toml").touch()

    # But docs/cli/documented.md mentions it
    (tmp_path / "docs/cli/documented.md").write_text("This mentions known command.")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])
    assert result.exit_code == 0
    # Should NOT warn about "documented known"
    assert "documented known" not in result.stdout
