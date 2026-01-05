
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch
from devbase.main import app

runner = CliRunner()

def test_pkm_journal_subprocess_secure(tmp_path):
    """
    Test that pkm journal calls subprocess.run with a list of arguments and shell=False (default).
    This ensures we don't have shell injection vulnerabilities.
    """
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

        assert result.exit_code == 0
        assert mock_run.called

        args, kwargs = mock_run.call_args
        command = args[0]
        is_shell = kwargs.get('shell', False)

        # Verify shell=True is NOT used
        assert is_shell is False
        # Verify command is a list
        assert isinstance(command, list)
        assert command[0] == "code"


def test_pkm_icebox_subprocess_secure(tmp_path):
    """
    Test that pkm icebox calls subprocess.run with a list of arguments and shell=False.
    """
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

        assert result.exit_code == 0
        assert mock_run.called

        args, kwargs = mock_run.call_args
        command = args[0]
        is_shell = kwargs.get('shell', False)

        assert is_shell is False
        assert isinstance(command, list)
        assert command[0] == "code"
