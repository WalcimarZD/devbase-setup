import subprocess
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.commands.pkm import app

runner = CliRunner()

def test_journal_command_injection_fix(tmp_path):
    # Setup mock workspace
    root = tmp_path
    (root / "10-19_KNOWLEDGE" / "12_private-vault" / "journal").mkdir(parents=True)

    # Mock context to return our tmp_path as root
    # We can inject it via obj

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value="/usr/bin/code"):

        # Invoke command
        result = runner.invoke(app, ["journal"], obj={"root": root})

        # Verify execution
        assert result.exit_code == 0

        # Check that subprocess.run was called safely
        # It should be called with a list, NOT a string with shell=True
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args

        # Security Assertion: verify shell is NOT True (default is False)
        assert kwargs.get("shell") is not True, "Command executed with shell=True (VULNERABLE!)"

        # Verify it passed a list of arguments
        cmd_args = args[0]
        assert isinstance(cmd_args, list), "Command arguments should be a list"
        assert cmd_args[0] == "code", "Should call 'code'"

        # Verify the path is correct
        # The filename depends on current date, so we just check it ends with .md and is in the path
        assert str(cmd_args[1]).endswith(".md")

def test_icebox_command_injection_fix(tmp_path):
    root = tmp_path
    (root / "00-09_SYSTEM" / "02_planning").mkdir(parents=True)
    icebox_file = root / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_file.touch()

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value="/usr/bin/code"):

        result = runner.invoke(app, ["icebox"], obj={"root": root})

        assert result.exit_code == 0

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args

        assert kwargs.get("shell") is not True, "Command executed with shell=True (VULNERABLE!)"

        cmd_args = args[0]
        assert isinstance(cmd_args, list)
        assert cmd_args[0] == "code"
        assert str(cmd_args[1]) == str(icebox_file)

def test_journal_command_no_code_installed(tmp_path):
    root = tmp_path

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value=None): # Mock code NOT installed

        result = runner.invoke(app, ["journal"], obj={"root": root})

        assert result.exit_code == 0
        # Should NOT call subprocess if code is missing
        mock_run.assert_not_called()
        assert "VS Code not found" in result.stdout or "Opening" in result.stdout # Depending on how we implement the warning
