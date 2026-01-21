import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from devbase.main import app
import os

runner = CliRunner()

def test_audit_run_basic(tmp_path):
    """Test that audit run executes without error."""
    # Create fake structure
    (tmp_path / "src" / "devbase" / "commands").mkdir(parents=True)
    (tmp_path / "src" / "devbase" / "commands" / "fake_cmd.py").write_text("""
import typer
app = typer.Typer()
@app.command("fake")
def fake_command(): pass
""")
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies=["requests"]')
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide\n")
    # Need .devbase_state.json for workspace detection if we don't force root (but we will force root)
    (tmp_path / ".devbase_state.json").write_text("{}")

    # We must pass --root to main.py so it populates ctx.obj["root"]
    # And we must ensure that the audit command uses that root.
    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    print(result.stdout)
    assert result.exit_code == 0
    assert "Auditoria de Consistência do DevBase" in result.stdout
    assert "Resumo do Relatório" in result.stdout

def test_audit_detects_undocumented_cli(tmp_path):
    """Test that audit detects undocumented commands."""
    (tmp_path / "src" / "devbase" / "commands").mkdir(parents=True)
    (tmp_path / "src" / "devbase" / "commands" / "secret.py").write_text("""
import typer
app = typer.Typer()
@app.command("ninja")
def ninja_cmd(): pass
""")
    (tmp_path / "USAGE-GUIDE.md").write_text("# Guide\n") # Empty guide
    (tmp_path / ".devbase_state.json").write_text("{}")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run"])

    assert "secret ninja" in result.stdout
    assert "⚠️" in result.stdout

def test_audit_fix_cli(tmp_path):
    """Test that audit --fix updates USAGE-GUIDE.md."""
    (tmp_path / "src" / "devbase" / "commands").mkdir(parents=True)
    (tmp_path / "src" / "devbase" / "commands" / "secret.py").write_text("""
import typer
app = typer.Typer()
@app.command("ninja")
def ninja_cmd(): pass
""")
    guide = tmp_path / "USAGE-GUIDE.md"
    guide.write_text("# Guide\n")
    (tmp_path / ".devbase_state.json").write_text("{}")

    result = runner.invoke(app, ["--root", str(tmp_path), "audit", "run", "--fix"])

    assert result.exit_code == 0
    content = guide.read_text()
    assert "Comandos Novos/Não Documentados" in content
    assert "devbase secret ninja" in content
