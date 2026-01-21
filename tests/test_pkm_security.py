import pytest
from unittest.mock import patch
from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Verify pkm journal does not use shell=True for opening editor."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])
        assert result.exit_code == 0

        # Check calls
        assert mock_run.called, "subprocess.run should have been called"
        args, kwargs = mock_run.call_args

        # Security assertions
        assert kwargs.get("shell") is not True, "subprocess.run called with shell=True"
        assert isinstance(args[0], list), "subprocess.run should use list args"
        assert args[0][0] == "code", "First argument should be 'code'"

def test_pkm_icebox_security(tmp_path):
    """Verify pkm icebox does not use shell=True for opening editor."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file so it opens it instead of returning error
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])
        assert result.exit_code == 0

        # Check calls
        assert mock_run.called, "subprocess.run should have been called"
        args, kwargs = mock_run.call_args

        # Security assertions
        assert kwargs.get("shell") is not True, "subprocess.run called with shell=True"
        assert isinstance(args[0], list), "subprocess.run should use list args"
        assert args[0][0] == "code", "First argument should be 'code'"
