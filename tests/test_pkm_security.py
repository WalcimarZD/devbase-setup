from typer.testing import CliRunner
from devbase.main import app
from pathlib import Path
from unittest.mock import patch, MagicMock

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Test 'pkm journal' uses safe open_in_vscode instead of shell=True."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Mock open_in_vscode to verify it's called
    with patch("devbase.commands.pkm.open_in_vscode") as mock_open:
        # Also mock subprocess in pkm.py to ensure it's NOT called directly
        # Note: We need to patch where it is imported. Since it was imported inside the function,
        # we can't easily patch it globally unless we patch subprocess module itself.
        # But if we refactor to use open_in_vscode, the import will be gone or unused.

        result = runner.invoke(
            app,
            ["--root", str(tmp_path), "pkm", "journal"]
        )

        assert result.exit_code == 0
        assert "Opening" in result.stdout

        # Verify open_in_vscode was called
        mock_open.assert_called_once()
        args, _ = mock_open.call_args
        assert args[0].name.startswith("weekly-")

def test_pkm_icebox_security(tmp_path):
    """Test 'pkm icebox' uses safe open_in_vscode instead of shell=True."""
    # Setup workspace
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Create icebox file needed for the command
    icebox_path = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_path.parent.mkdir(parents=True, exist_ok=True)
    icebox_path.touch()

    with patch("devbase.commands.pkm.open_in_vscode") as mock_open:
        result = runner.invoke(
            app,
            ["--root", str(tmp_path), "pkm", "icebox"]
        )

        assert result.exit_code == 0
        assert "Opening" in result.stdout

        # Verify open_in_vscode was called
        mock_open.assert_called_once()
        args, _ = mock_open.call_args
        assert args[0].name == "icebox.md"
