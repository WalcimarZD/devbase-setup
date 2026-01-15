"""
Security tests for PKM commands.
Verifies that commands do not use shell=True and handle paths correctly.
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """
    Test that 'pkm journal' uses secure subprocess call (no shell=True)
    when opening the journal file.
    """
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Mock subprocess.run to verify arguments
    with patch("subprocess.run") as mock_run:
        # Run command without arguments to trigger "Open in editor" logic
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0

        # Verify subprocess was called
        assert mock_run.called

        # Get the arguments of the call
        args, kwargs = mock_run.call_args
        command_args = args[0]

        # SECURITY CHECKS:
        # 1. shell must NOT be True (default is False, so check it's not explicitly True)
        assert kwargs.get("shell") is not True, "Security Risk: shell=True detected!"

        # 2. command must be a list, not a string
        assert isinstance(command_args, list), "Security Risk: Command should be a list, not a string!"

        # 3. command should start with "code"
        assert command_args[0] == "code"

        # 4. second argument should be the file path
        assert str(tmp_path) in command_args[1]

def test_pkm_icebox_security(tmp_path):
    """
    Test that 'pkm icebox' uses secure subprocess call (no shell=True)
    when opening the icebox file.
    """
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file so it exists (otherwise command might fail early or just error out)
    # The command checks if file exists before opening.
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    # Mock subprocess.run
    with patch("subprocess.run") as mock_run:
        # Run command without arguments to trigger "Open in editor" logic
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0

        # Verify subprocess was called
        assert mock_run.called

        # Get the arguments
        args, kwargs = mock_run.call_args
        command_args = args[0]

        # SECURITY CHECKS:
        assert kwargs.get("shell") is not True, "Security Risk: shell=True detected!"
        assert isinstance(command_args, list), "Security Risk: Command should be a list!"
        assert command_args[0] == "code"
        assert str(icebox_path) == command_args[1]
