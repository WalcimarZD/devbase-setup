
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from devbase.main import app

runner = CliRunner()

def test_ops_backup_spinner(tmp_path):
    """
    Test 'ops backup' runs and utilizes the spinner.
    We mock shutil.copytree to avoid heavy IO and verify the spinner interaction.
    """
    # Setup minimal workspace
    (tmp_path / ".devbase_state.json").write_text("{}")

    # Mock shutil.copytree and Path.mkdir
    with patch("shutil.copytree") as mock_copy, \
         patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("devbase.commands.operations.console.status") as mock_status:

        # Configure the mock context manager for status
        mock_status_ctx = MagicMock()
        mock_status.return_value = mock_status_ctx
        mock_status_ctx.__enter__.return_value = None

        result = runner.invoke(app, ["--root", str(tmp_path), "ops", "backup"])

        assert result.exit_code == 0
        assert "Creating backup..." in result.stdout
        assert "Backup created successfully" in result.stdout

        # Verify copytree was called
        assert mock_copy.called

        # Verify spinner was used
        assert mock_status.called
        # Check that the status message contains expected text
        # Since status is called with positional args, checking args[0]
        args, _ = mock_status.call_args
        assert "Backing up workspace" in args[0]
