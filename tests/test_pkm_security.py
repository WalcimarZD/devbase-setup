"""
Security tests for PKM commands.
"""
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

# Mock modules to avoid importing dependencies that might not be present or initialized
sys.modules["devbase.services.knowledge_db"] = MagicMock()
sys.modules["devbase.services.knowledge_graph"] = MagicMock()
sys.modules["devbase.adapters.storage"] = MagicMock()
sys.modules["devbase.adapters.storage.duckdb_adapter"] = MagicMock()
sys.modules["devbase.utils.telemetry"] = MagicMock()

from devbase.commands import pkm

def test_pkm_journal_command_injection_prevention():
    """Test that journal command avoids shell injection."""
    # Setup malicious root path
    malicious_root = Path('/tmp/innocent"; echo "PWNED')

    # Mock context
    ctx = MagicMock()
    ctx.obj = {"root": malicious_root}

    with patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("shutil.which", return_value="/usr/bin/code"):

        # Run command
        pkm.journal(ctx, entry=None)

        # Verify
        assert mock_run.called
        args, kwargs = mock_run.call_args
        cmd = args[0]
        shell = kwargs.get("shell", False)

        # Assertions
        assert shell is False, "Command should not run in shell"
        assert isinstance(cmd, list), "Command should be a list"
        assert cmd[0] == "/usr/bin/code", "Should call code executable"
        assert str(malicious_root) in cmd[1], "Path should be passed as argument"

def test_pkm_icebox_command_injection_prevention():
    """Test that icebox command avoids shell injection."""
    malicious_root = Path('/tmp/innocent"; echo "PWNED')
    ctx = MagicMock()
    ctx.obj = {"root": malicious_root}

    with patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("shutil.which", return_value="/usr/bin/code"):

        pkm.icebox(ctx, idea=None)

        assert mock_run.called
        args, kwargs = mock_run.call_args
        cmd = args[0]
        shell = kwargs.get("shell", False)

        assert shell is False
        assert isinstance(cmd, list)
        assert cmd[0] == "/usr/bin/code"
