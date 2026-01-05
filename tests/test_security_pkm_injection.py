
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.commands.pkm import app
import datetime

runner = CliRunner()

@pytest.fixture
def mock_root(tmp_path):
    root = tmp_path / "devbase_root"
    root.mkdir()
    (root / "10-19_KNOWLEDGE" / "12_private-vault" / "journal").mkdir(parents=True)
    (root / "00-09_SYSTEM" / "02_planning").mkdir(parents=True)
    # create icebox file
    (root / "00-09_SYSTEM" / "02_planning" / "icebox.md").touch()
    return root

def test_journal_command_safe_subprocess(mock_root):
    # This test verifies the FIXED state (shell=False, list args)

    with patch("subprocess.run") as mock_run:
        with patch("datetime.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.isocalendar.return_value = (2024, 1, 1)
            mock_now.strftime.return_value = "2024-01-01"
            mock_datetime.now.return_value = mock_now

            # invoke journal
            result = runner.invoke(app, ["journal"], obj={"root": mock_root})

            assert result.exit_code == 0

            # Verify subprocess.run was called SAFELY
            calls = mock_run.call_args_list
            assert len(calls) > 0

            args, kwargs = calls[0]
            # shell should be False (default) or not True
            assert kwargs.get("shell") is not True, "shell=True should NOT be used"

            # Args should be a list
            assert isinstance(args[0], list), "Command should be a list, not a string"
            assert args[0][0] == "code"
            # Second arg should be the path
            assert str(mock_root) in str(args[0][1])

def test_icebox_command_safe_subprocess(mock_root):
    # This test verifies the FIXED state

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["icebox"], obj={"root": mock_root})

        assert result.exit_code == 0

        calls = mock_run.call_args_list
        assert len(calls) > 0

        args, kwargs = calls[0]
        assert kwargs.get("shell") is not True
        assert isinstance(args[0], list)
        assert args[0][0] == "code"
