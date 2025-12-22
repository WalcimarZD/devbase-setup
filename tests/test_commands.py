"""
Tests for core commands (setup, doctor, hydrate).
"""
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


def test_core_help():
    """Test core command group help."""
    result = runner.invoke(app, ["core", "--help"])
    assert result.exit_code == 0
    assert "Core workspace commands" in result.stdout


def test_dev_help():
    """Test dev command group help."""
    result = runner.invoke(app, ["dev", "--help"])
    assert result.exit_code == 0
    assert "Development commands" in result.stdout


def test_ops_help():
    """Test ops command group help."""
    result = runner.invoke(app, ["ops", "--help"])
    assert result.exit_code == 0
    assert "Operations" in result.stdout


def test_doctor_without_workspace(tmp_path, monkeypatch):
    """Test doctor command when no workspace exists."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEVBASE_ROOT", str(tmp_path / "nonexistent"))
    
    result = runner.invoke(app, ["core", "doctor"])
    # Should prompt for workspace creation
    assert "workspace" in result.stdout.lower() or result.exit_code != 0
