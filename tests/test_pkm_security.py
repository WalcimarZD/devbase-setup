import subprocess
from unittest.mock import patch
from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_journal_open_secure(tmp_path):
    """
    Test that 'pkm journal' uses secure subprocess call (list args, no shell).
    """
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0

        # Verify call args
        args, kwargs = mock_run.call_args

        # SECURE BEHAVIOR: shell should NOT be True
        assert not kwargs.get("shell"), "shell=True should NOT be used"

        # Verify the command is a list
        cmd = args[0]
        assert isinstance(cmd, list), "Command should be a list"
        assert cmd[0] == "code", "First argument should be 'code'"
        # Second argument should be the path
        assert "weekly-" in cmd[1], "Second argument should be the file path"

def test_icebox_open_secure(tmp_path):
    """
    Test that 'pkm icebox' uses secure subprocess call (list args, no shell).
    """
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Ensure icebox file exists
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.write_text("# Icebox")

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0

        # Verify call args
        args, kwargs = mock_run.call_args

        # SECURE BEHAVIOR: shell should NOT be True
        assert not kwargs.get("shell"), "shell=True should NOT be used"

        # Verify the command is a list
        cmd = args[0]
        assert isinstance(cmd, list), "Command should be a list"
        assert cmd[0] == "code", "First argument should be 'code'"
        assert str(icebox_path) == cmd[1], "Second argument should be the correct file path"
