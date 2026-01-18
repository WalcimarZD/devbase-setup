import subprocess
import shutil
from unittest.mock import patch
from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_pkm_journal_opens_securely(tmp_path):
    """Test that 'pkm journal' opens file securely (no shell=True)."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Mock subprocess.run AND shutil.which
    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value="/usr/bin/code"):

        # Invoke command
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0

        # Verify subprocess was called
        assert mock_run.called
        args, kwargs = mock_run.call_args

        # Security assertion: shell must NOT be True
        assert kwargs.get("shell") is not True, "subprocess.run called with shell=True!"

        # Argument assertion: First arg should be a list, not a string
        assert isinstance(args[0], list), "subprocess.run called with string instead of list!"
        assert args[0][0] == "code"

def test_pkm_icebox_opens_securely(tmp_path):
    """Test that 'pkm icebox' opens file securely (no shell=True)."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("subprocess.run") as mock_run, \
         patch("shutil.which", return_value="/usr/bin/code"):

        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0

        assert mock_run.called
        args, kwargs = mock_run.call_args

        assert kwargs.get("shell") is not True, "subprocess.run called with shell=True!"
        assert isinstance(args[0], list), "subprocess.run called with string instead of list!"
        assert args[0][0] == "code"
