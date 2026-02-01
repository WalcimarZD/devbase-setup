import subprocess
from unittest.mock import patch
from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Test that pkm journal does not use shell=True for opening files."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # We mock subprocess.run to verify how it's called
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0

        # Verify subprocess.run was called
        if not mock_run.called:
             # Check output to see if it failed for other reasons
             print(result.stdout)
        assert mock_run.called

        # Get the arguments of the call
        args, kwargs = mock_run.call_args

        # SECURITY CHECK: shell must NOT be True
        assert kwargs.get("shell") is not True, "subprocess.run called with shell=True!"

        # Verify it uses a list for arguments, not a string
        cmd_args = args[0]
        assert isinstance(cmd_args, list), f"subprocess.run called with string instead of list: {cmd_args}"
        assert cmd_args[0] == "code", "Expected 'code' as first argument"

def test_pkm_icebox_security(tmp_path):
    """Test that pkm icebox does not use shell=True for opening files."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file so the command doesn't return early
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    # Note: we need to patch the subprocess imported in the module, not global subprocess
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0

        # Verify subprocess.run was called
        if not mock_run.called:
             print(result.stdout)
        assert mock_run.called

        # Get the arguments of the call
        args, kwargs = mock_run.call_args

        # SECURITY CHECK: shell must NOT be True
        assert kwargs.get("shell") is not True, "subprocess.run called with shell=True!"

        # Verify it uses a list for arguments
        cmd_args = args[0]
        assert isinstance(cmd_args, list), f"subprocess.run called with string instead of list: {cmd_args}"
        assert cmd_args[0] == "code", "Expected 'code' as first argument"
