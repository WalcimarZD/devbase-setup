
import subprocess
from unittest import mock
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_journal_command_injection_reproduction(tmp_path):
    """
    Test reproducing the command injection vulnerability in 'pkm journal'.
    It verifies that subprocess.run is called with shell=True and a string command.
    """
    # Setup workspace to ensure 'root' context is valid
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # We patch subprocess.run to intercept the call
    with mock.patch("subprocess.run") as mock_run, \
         mock.patch("shutil.which", return_value="/usr/bin/code"):
        # Invoke 'pkm journal' without arguments -> triggers "open in editor"
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        # Verify the command attempted to open the file
        assert result.exit_code == 0
        assert "Opening" in result.stdout

        # Assert that subprocess.run was called
        assert mock_run.called

        # Get the arguments of the last call
        args, kwargs = mock_run.call_args

        # SECURITY FIX VERIFICATION:
        # We expect shell=False (default, or None)
        assert not kwargs.get("shell"), "Expected shell=False"

        # The command should be a list: ["code", "path"]
        cmd_arg = args[0]
        assert isinstance(cmd_arg, list), "Expected command to be a list"
        # We expect resolved path if shutil found it, or "code"
        assert "code" in cmd_arg[0]
        assert str(cmd_arg[1]).endswith(".md")

def test_icebox_command_injection_reproduction(tmp_path):
    """
    Test reproducing the command injection vulnerability in 'pkm icebox'.
    """
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Manually create the icebox file since 'pkm icebox' expects it to exist
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.write_text("# Icebox\n")

    with mock.patch("subprocess.run") as mock_run, \
         mock.patch("shutil.which", return_value="/usr/bin/code"):
        # Now open it
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert "Opening" in result.stdout
        assert mock_run.called

        args, kwargs = mock_run.call_args

        # SECURITY FIX VERIFICATION
        assert not kwargs.get("shell")
        assert isinstance(args[0], list)
        assert "code" in args[0][0]
