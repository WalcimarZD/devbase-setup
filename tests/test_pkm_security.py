import subprocess
import pytest
from typer.testing import CliRunner
from unittest import mock
from pathlib import Path
from devbase.main import app

runner = CliRunner()

@pytest.fixture
def mock_subprocess():
    with mock.patch("subprocess.run") as mock_run:
        yield mock_run

def test_pkm_journal_opens_with_shell_true(tmp_path, mock_subprocess):
    """
    Test that 'pkm journal' without args opens the file using list args (Fixed).
    """
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Run pkm journal without args
    result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

    # Verify exit code
    assert result.exit_code == 0

    # Verify subprocess.run was called
    assert mock_subprocess.called

    # Get the arguments of the call
    args, kwargs = mock_subprocess.call_args

    # Check if shell=True is NOT in kwargs or is False
    assert not kwargs.get("shell")

    # Check if the command is a list
    command = args[0]
    assert isinstance(command, list)
    assert command[0] == "code"
    # command[1] will be the path

def test_pkm_icebox_opens_with_shell_true(tmp_path, mock_subprocess):
    """
    Test that 'pkm icebox' without args opens the file using list args (Fixed).
    """
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Ensure icebox file exists
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.write_text("Icebox")

    # Run pkm icebox without args
    result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

    # Verify exit code
    assert result.exit_code == 0

    # Verify subprocess.run was called
    assert mock_subprocess.called

    # Get the arguments of the call
    args, kwargs = mock_subprocess.call_args

    # Check if shell=True is NOT in kwargs or is False
    assert not kwargs.get("shell")

    # Check if the command is a list
    command = args[0]
    assert isinstance(command, list)
    assert command[0] == "code"
