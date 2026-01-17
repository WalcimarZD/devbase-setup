"""
Tests for the Consistency Audit command.
"""
from pathlib import Path
from typer.testing import CliRunner
import toml

from devbase.main import app
from devbase.commands import audit

runner = CliRunner()

def test_audit_run_clean(tmp_path):
    """Test audit runs cleanly on a mocked consistent environment."""
    # Setup mock environment
    root = tmp_path
    (root / ".devbase_state.json").write_text("{}") # Mock workspace

    # 1. src/devbase structure
    (root / "src/devbase/commands").mkdir(parents=True)
    (root / "src/devbase/commands/test_cmd.py").write_text('@app.command("foo")\ndef foo(): pass')

    # 2. Docs
    (root / "docs").mkdir()
    (root / "USAGE-GUIDE.md").write_text("devbase test_cmd foo")
    (root / "ARCHITECTURE.md").write_text("test-lib")
    (root / "README.md").write_text("test-lib")
    (root / "TECHNICAL_DESIGN_DOC.md").write_text("hot_fts cold_fts") # tables

    # 3. pyproject.toml
    (root / "pyproject.toml").write_text('[project]\ndependencies = ["test-lib"]')

    # 4. DB Code
    (root / "src/devbase/adapters/storage").mkdir(parents=True)
    (root / "src/devbase/adapters/storage/duckdb_adapter.py").write_text('CREATE TABLE IF NOT EXISTS hot_fts ...')

    # Run audit
    # We must mock Path.cwd() because audit uses it.
    # But audit.py uses Path.cwd() which we can't easily mock via CliRunner without monkeypatching.
    # Wait, audit.py uses Path.cwd() directly.
    # We should update audit.py to accept root arg or use ctx.obj["root"].
    # But for now, let's use monkeypatch.

    # Using chdir context manager for the test
    # We pass --root explicitly to bypass workspace detection
    result = runner.invoke(app, ["--root", str(root), "audit", "run"])

    assert result.exit_code == 0
    assert "System is consistent" in result.stdout

def test_audit_detects_missing_deps(tmp_path):
    """Test audit detects missing dependencies."""
    root = tmp_path
    (root / ".devbase_state.json").write_text("{}")
    (root / "pyproject.toml").write_text('[project]\ndependencies = ["new-lib"]')
    (root / "ARCHITECTURE.md").write_text("") # Missing
    (root / "README.md").write_text("") # Missing
    (root / "src/devbase").mkdir(parents=True)

    # Mock other files to avoid noise
    (root / "USAGE-GUIDE.md").write_text("")
    (root / "TECHNICAL_DESIGN_DOC.md").write_text("")

    result = runner.invoke(app, ["--root", str(root), "audit", "run"])

    assert "Dependencies missing in ARCHITECTURE.md: new-lib" in result.stdout
    assert "Dependencies missing in README.md: new-lib" in result.stdout

def test_audit_detects_undocumented_cli(tmp_path):
    """Test audit detects undocumented CLI commands."""
    root = tmp_path
    (root / ".devbase_state.json").write_text("{}")
    (root / "src/devbase/commands").mkdir(parents=True)
    (root / "src/devbase/commands/mycmd.py").write_text('@app.command("secret")\ndef secret(): pass')

    (root / "USAGE-GUIDE.md").write_text("nothing here")
    (root / "pyproject.toml").write_text("")

    result = runner.invoke(app, ["--root", str(root), "audit", "run"])

    assert "Undocumented commands in USAGE-GUIDE.md" in result.stdout
    assert "devbase mycmd secret" in result.stdout

def test_audit_detects_db_inconsistency(tmp_path):
    """Test audit detects undocumented DB tables."""
    root = tmp_path
    (root / ".devbase_state.json").write_text("{}")
    (root / "docs").mkdir()
    (root / "docs/TECHNICAL_DESIGN_DOC.md").write_text("hot_fts") # Missing cold_fts

    (root / "src/devbase/adapters/storage").mkdir(parents=True)
    (root / "src/devbase/adapters/storage/duckdb_adapter.py").write_text('CREATE TABLE IF NOT EXISTS cold_fts ...')

    (root / "pyproject.toml").write_text("")
    (root / "USAGE-GUIDE.md").write_text("")

    result = runner.invoke(app, ["--root", str(root), "audit", "run"])

    assert "Tables found in code but missing in TECHNICAL_DESIGN_DOC.md: cold_fts" in result.stdout
