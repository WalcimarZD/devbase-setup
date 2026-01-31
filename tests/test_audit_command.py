"""
Tests for the Consistency Audit Command.
Verifies logic for dependency checking, CLI consistency, and DB integrity.
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_audit_run_clean(tmp_path):
    """Test audit passes on a clean, consistent workspace."""
    # Setup minimal consistent state
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["typer"]\n')
    (tmp_path / "ARCHITECTURE.md").write_text("# Arch\nTyper used for CLI.\n")
    (tmp_path / "README.md").write_text("# Readme\nTyper used.\n")
    (tmp_path / "src/devbase/commands").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/cli").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/devbase/services").mkdir(parents=True, exist_ok=True)

    # DB consistency
    (tmp_path / "src/devbase/services/knowledge_db.py").write_text("class DB:\n  pass\n# hot_fts\n# cold_fts\n")
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").write_text("# TDD\nIncludes hot_fts and cold_fts tables.\n")

    # USAGE GUIDE
    (tmp_path / "USAGE-GUIDE.md").write_text("# Usage\n")

    # Mock git to fail so we rely on mtime (or valid git return)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    # Should not contain warnings
    assert "⚠️" not in result.stdout
    assert "Sistema consistente" in result.stdout

def test_audit_detects_missing_deps(tmp_path):
    """Test audit detects dependencies missing from docs."""
    # Setup mismatch
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["secret-lib"]\n')
    (tmp_path / "ARCHITECTURE.md").write_text("# Arch\nNo mention of secret lib.\n")
    (tmp_path / "README.md").write_text("# Readme\n")

    # Dummy files to prevent other errors
    (tmp_path / "src/devbase/commands").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/devbase/services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "USAGE-GUIDE.md").touch()
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").touch()
    (tmp_path / "src/devbase/services/knowledge_db.py").touch()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    assert "secret-lib" in result.stdout
    assert "ausentes na ARCHITECTURE.md" in result.stdout

def test_audit_detects_missing_tables(tmp_path):
    """Test audit detects missing hot_fts/cold_fts in docs."""
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "src/devbase/commands").mkdir(parents=True, exist_ok=True)
    (tmp_path / "USAGE-GUIDE.md").touch()

    # DB has them, docs don't
    (tmp_path / "src/devbase/services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/devbase/services/knowledge_db.py").write_text("hot_fts = 1\ncold_fts = 2")
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").write_text("# TDD\nNo tables mentioned.")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert result.exit_code == 0
    assert "hot_fts" in result.stdout
    assert "cold_fts" in result.stdout
    assert "ausentes na TECHNICAL_DESIGN_DOC.md" in result.stdout

def test_audit_cli_docs_update(tmp_path):
    """Test audit detects and fixes undocumented commands."""
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "src/devbase/services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").touch()
    (tmp_path / "src/devbase/services/knowledge_db.py").touch()

    # Command exists
    cmd_dir = tmp_path / "src/devbase/commands"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    (cmd_dir / "secret.py").write_text('@app.command("hidden")\ndef hidden(): pass')

    # Docs exist but missing command
    (tmp_path / "USAGE-GUIDE.md").write_text("# Usage\n")

    # Run with fix
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run", "--fix"])

    assert result.exit_code == 0
    assert "Comandos não documentados" in result.stdout
    assert "secret hidden" in result.stdout

    # Verify fix
    content = (tmp_path / "USAGE-GUIDE.md").read_text()
    assert "devbase secret hidden" in content

def test_audit_changelog_update(tmp_path):
    """Test audit updates changelog if changes detected."""
    # Mock everything valid except changelog needs update
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "src/devbase/commands").mkdir(parents=True, exist_ok=True)
    (tmp_path / "USAGE-GUIDE.md").touch()
    (tmp_path / "src/devbase/services").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/devbase/services/knowledge_db.py").touch()
    (tmp_path / "docs/TECHNICAL_DESIGN_DOC.md").touch()

    # Changelog exists but no draft section
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## 1.0.0\n- Old stuff\n")

    # Mock git detection success
    with patch("subprocess.run") as mock_run:
        # Mock git log success return
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "src/devbase/new_feature.py\n"

        result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run", "--fix"])

    assert result.exit_code == 0
    assert "Verificando Changelog" in result.stdout

    content = (tmp_path / "CHANGELOG.md").read_text()
    assert "[In Progress] - Draft" in content
