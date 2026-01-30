import subprocess
from unittest.mock import patch
from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Test 'pkm journal' uses safe subprocess call."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0

        # Verify call args
        assert mock_run.called
        args, kwargs = mock_run.call_args

        # Check that the first argument is a list (safe)
        cmd_arg = args[0]
        assert isinstance(cmd_arg, list), f"Command should be a list, got {type(cmd_arg)}: {cmd_arg}"
        assert cmd_arg[0] == "code" or cmd_arg[0].endswith("code")
        assert kwargs.get("shell") is not True

def test_pkm_icebox_security(tmp_path):
    """Test 'pkm icebox' uses safe subprocess call."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file because the command checks for existence
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0
        assert mock_run.called
        args, kwargs = mock_run.call_args

        cmd_arg = args[0]
        assert isinstance(cmd_arg, list), f"Command should be a list, got {type(cmd_arg)}: {cmd_arg}"
        assert kwargs.get("shell") is not True
