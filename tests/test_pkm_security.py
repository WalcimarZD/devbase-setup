import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from pathlib import Path
from devbase.commands.pkm import app

runner = CliRunner()

@pytest.fixture
def mock_root(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".devbase_state.json").write_text("{}")

    # Create required directories
    (root / "10-19_KNOWLEDGE" / "12_private-vault" / "journal").mkdir(parents=True)
    (root / "00-09_SYSTEM" / "02_planning").mkdir(parents=True)
    (root / "00-09_SYSTEM" / "02_planning" / "icebox.md").write_text("# Icebox")

    return root

def test_journal_command_injection_check(mock_root):
    """
    Verify that opening journal does not use shell=True and passes arguments as a list.
    """
    with patch("subprocess.run") as mock_run:
        # We need to inject the mock root into the context
        # Since we can't easily inject context obj with CliRunner in this specific app setup
        # without modifying main.py or using a complex fixture,
        # we will patch the context object retrieval inside the command if necessary.
        # However, typer CliRunner accepts an obj argument.

        result = runner.invoke(app, ["journal"], obj={"root": mock_root})

        # We expect the command to fail if it can't find 'code', but we mocked subprocess.run
        assert result.exit_code == 0

        # Verify call args
        args, kwargs = mock_run.call_args
        command = args[0]

        # Security Check: shell should NOT be True
        assert kwargs.get("shell") is not True, "Security: shell=True usage detected!"

        # Security Check: command should be a list, not a string
        assert isinstance(command, list), "Security: Command should be a list of arguments"
        assert command[0] == "code", "Security: Should invoke code directly"

def test_icebox_command_injection_check(mock_root):
    """
    Verify that opening icebox does not use shell=True and passes arguments as a list.
    """
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["icebox"], obj={"root": mock_root})

        assert result.exit_code == 0

        args, kwargs = mock_run.call_args
        command = args[0]

        assert kwargs.get("shell") is not True, "Security: shell=True usage detected!"
        assert isinstance(command, list), "Security: Command should be a list of arguments"
        assert command[0] == "code"
