"""
Security tests for PKM commands.
Verifies prevention of command injection vulnerabilities.
"""
from unittest.mock import patch

from typer.testing import CliRunner

from devbase.main import app

runner = CliRunner()

def test_pkm_journal_security(tmp_path):
    """Test that 'pkm journal' uses secure subprocess calls."""
    # Setup minimal structure
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # We patch subprocess.run globally since it is imported inside the function
    with patch("subprocess.run") as mock_run:
        # Mock shutil.which to ensure it finds 'code' or returns a predictable path
        # Note: The fix will use shutil.which, so we mock it.
        # The current vulnerable code doesn't use it, but that doesn't hurt.
        with patch("shutil.which", return_value="/usr/bin/code"):
            result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "journal"])

            assert result.exit_code == 0

            # Verify subprocess call
            assert mock_run.called
            args, kwargs = mock_run.call_args

            # Security checks
            # This assertion checks that shell=True is NOT used
            assert kwargs.get("shell") is False, "Command injection risk: shell=True used"

            # This assertion checks that arguments are passed as a list
            assert isinstance(args[0], list), "Command injection risk: args not a list"

            # This checks that we are using the resolved executable
            # (Flexible check to allow for 'code' or '/usr/bin/code')
            cmd = args[0][0]
            assert "code" in cmd, "Executable not found or incorrect"

def test_pkm_icebox_security(tmp_path):
    """Test that 'pkm icebox' uses secure subprocess calls."""
    # Setup minimal structure
    runner.invoke(app, ["--root", str(tmp_path), "core", "setup", "--no-interactive"])

    # Ensure icebox file exists so the command proceeds to open it
    icebox_file = tmp_path / "00-09_SYSTEM" / "02_planning" / "icebox.md"
    icebox_file.parent.mkdir(parents=True, exist_ok=True)
    icebox_file.write_text("Test Icebox")

    with patch("subprocess.run") as mock_run:
         with patch("shutil.which", return_value="/usr/bin/code"):
            result = runner.invoke(app, ["--root", str(tmp_path), "pkm", "icebox"])

            assert result.exit_code == 0

            # Verify subprocess call
            assert mock_run.called
            args, kwargs = mock_run.call_args

            # Security checks
            assert kwargs.get("shell") is False, "Command injection risk: shell=True used"
            assert isinstance(args[0], list), "Command injection risk: args not a list"
            cmd = args[0][0]
            assert "code" in cmd, "Executable not found or incorrect"
