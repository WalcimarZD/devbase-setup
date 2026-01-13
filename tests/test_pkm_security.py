import sys
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Test 'pkm journal' uses secure subprocess call."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Mock shutil.which to return true
    # Mock subprocess.run to verify arguments
    with patch("shutil.which", return_value="/usr/bin/code"), \
         patch("subprocess.run") as mock_run:

        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0
        assert "Opening" in result.stdout

        # Verify subprocess called correctly
        # It should NOT be called with shell=True
        # It should be called with a list: ["code", path]
        assert mock_run.called
        args, kwargs = mock_run.call_args
        cmd_list = args[0]

        assert isinstance(cmd_list, list)
        assert cmd_list[0] == "code"
        assert str(tmp_path) in cmd_list[1]
        assert kwargs.get("check") is False
        assert kwargs.get("shell") is not True

def test_pkm_icebox_security(tmp_path):
    """Test 'pkm icebox' uses secure subprocess call."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Ensure icebox file exists
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("shutil.which", return_value="/usr/bin/code"), \
         patch("subprocess.run") as mock_run:

        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0
        assert "Opening icebox.md" in result.stdout

        assert mock_run.called
        args, kwargs = mock_run.call_args
        cmd_list = args[0]

        assert isinstance(cmd_list, list)
        assert cmd_list[0] == "code"
        assert "icebox.md" in cmd_list[1]
        assert kwargs.get("check") is False
        assert kwargs.get("shell") is not True

def test_pkm_missing_code_editor(tmp_path):
    """Test graceful failure when 'code' is missing."""
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Ensure icebox file exists
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("shutil.which", return_value=None), \
         patch("subprocess.run") as mock_run:

        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0
        assert "not found in PATH" in result.stdout
        assert not mock_run.called
