import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from devbase.commands.pkm import app

runner = CliRunner()

def test_pkm_journal_secure_subprocess(tmp_path):
    """
    Test that pkm journal command uses secure subprocess call (no shell=True).
    """
    with patch("subprocess.run") as mock_run, \
         patch("shutil.which") as mock_which:

        # Simulate 'code' being available
        mock_which.return_value = "/usr/bin/code"

        result = runner.invoke(app, ["journal"], obj={"root": tmp_path})

        assert result.exit_code == 0

        # Verify it called subprocess.run
        assert mock_run.called

        # Verify it used SAFE arguments
        args, kwargs = mock_run.call_args
        assert kwargs.get("shell") is not True, "Security regression: shell=True was used!"

        cmd = args[0]
        assert isinstance(cmd, list), "Command should be a list for security"
        assert cmd[0] == "code"
        assert str(tmp_path) in cmd[1]

def test_pkm_icebox_secure_subprocess(tmp_path):
    """
    Test that pkm icebox command uses secure subprocess call (no shell=True).
    """
    # Setup icebox file
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which") as mock_which:

        mock_which.return_value = "/usr/bin/code"

        result = runner.invoke(app, ["icebox"], obj={"root": tmp_path})

        assert result.exit_code == 0
        assert mock_run.called

        # Verify SAFE arguments
        args, kwargs = mock_run.call_args
        assert kwargs.get("shell") is not True

        cmd = args[0]
        assert isinstance(cmd, list)
        assert cmd[0] == "code"
        assert str(icebox_path) == cmd[1]

def test_pkm_journal_no_code_editor(tmp_path):
    """
    Test graceful failure when 'code' is not in path.
    """
    with patch("subprocess.run") as mock_run, \
         patch("shutil.which") as mock_which:

        # Simulate 'code' NOT available
        mock_which.return_value = None

        result = runner.invoke(app, ["journal"], obj={"root": tmp_path})

        assert result.exit_code == 0
        assert not mock_run.called
        assert "VS Code ('code') not found" in result.stdout
