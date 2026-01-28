import subprocess
from unittest import mock
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Test that 'pkm journal' uses safe subprocess execution."""
    # Setup - must run setup to ensure root exists and is valid for ctx.obj["root"]
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Mock subprocess.run
    with mock.patch("subprocess.run") as mock_run:
        # Run journal command (opens editor)
        # Note: --root must be passed
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0

        # Verify call args
        assert mock_run.called
        args, kwargs = mock_run.call_args

        # We expect the first arg to be a list starting with "code"
        # If it fails (current code), args[0] will be a string and shell=True will be set
        assert isinstance(args[0], list), f"Expected list args, got: {args[0]}"
        assert args[0][0] == "code"

        # Ensure shell=True is NOT present or is False
        assert kwargs.get("shell", False) is False, "shell=True should not be used"

def test_pkm_icebox_security(tmp_path):
    """Test that 'pkm icebox' uses safe subprocess execution."""
    # Setup
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file so it tries to open it
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    # Mock subprocess.run
    with mock.patch("subprocess.run") as mock_run:
        # Run icebox command
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0

        # Verify call args
        assert mock_run.called
        args, kwargs = mock_run.call_args

        # We expect the first arg to be a list starting with "code"
        assert isinstance(args[0], list), f"Expected list args, got: {args[0]}"
        assert args[0][0] == "code"

        # Ensure shell=True is NOT present or is False
        assert kwargs.get("shell", False) is False, "shell=True should not be used"
