import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from devbase.commands.pkm import app
import subprocess

runner = CliRunner()

@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock:
        yield mock

@pytest.fixture
def mock_context():
    # Mocking the context object as it's used in commands to get 'root'
    return {"root": MagicMock(), "console": MagicMock()}

def test_journal_command_injection_fix(mock_subprocess, tmp_path):
    """
    Test that pkm journal command uses list-based subprocess call (secure).
    """
    # Create a dummy journal directory structure
    root = tmp_path
    journal_dir = root / "10-19_KNOWLEDGE" / "12_private-vault" / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["journal"], obj={"root": root})

    assert result.exit_code == 0

    assert mock_subprocess.called
    args, kwargs = mock_subprocess.call_args

    # Assert SECURE behavior
    assert kwargs.get("shell") is not True
    assert isinstance(args[0], list)
    assert args[0][0] == "code"
    # Ensure file path is passed as second argument
    assert str(root) in args[0][1]

def test_icebox_command_injection_fix(mock_subprocess, tmp_path):
    """
    Test that pkm icebox command uses list-based subprocess call (secure).
    """
    root = tmp_path
    (root / "00-09_SYSTEM" / "02_planning").mkdir(parents=True, exist_ok=True)
    (root / "00-09_SYSTEM" / "02_planning" / "icebox.md").touch()

    result = runner.invoke(app, ["icebox"], obj={"root": root})

    assert result.exit_code == 0

    assert mock_subprocess.called
    args, kwargs = mock_subprocess.call_args

    # Assert SECURE behavior
    assert kwargs.get("shell") is not True
    assert isinstance(args[0], list)
    assert args[0][0] == "code"
    assert "icebox.md" in args[0][1]
