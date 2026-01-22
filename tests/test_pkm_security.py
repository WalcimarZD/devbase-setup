import subprocess
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest
from typer.testing import CliRunner
from devbase.commands.pkm import app

class TestPkmSecurity(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_journal_safe_open(self, mock_run, mock_which):
        from devbase.commands.pkm import journal
        from typer import Context

        # Mock shutil.which to return a path
        mock_which.return_value = "/usr/bin/code"

        # Create a mock context
        root_path = Path("/tmp/mock_root")
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.obj = {"root": root_path}

        # Mock exists to avoid actual file creation logic if possible,
        # but journal checks existence.
        with patch('pathlib.Path.exists', return_value=True):
             # Call journal with no entry (opens editor)
            journal(mock_ctx, entry=None)

            # Assert subprocess.run was called
            self.assertTrue(mock_run.called, "subprocess.run should be called when code is available")

            # Get the args
            args, kwargs = mock_run.call_args

            # Check for security
            if kwargs.get('shell') is True:
                self.fail("subprocess.run called with shell=True! Vulnerable to command injection.")

            # Also check that args[0] is a list, not a string
            self.assertIsInstance(args[0], list, "subprocess.run should be called with a list of arguments")
            self.assertEqual(args[0][0], "/usr/bin/code", "First argument should be the resolved path to 'code'")

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_icebox_safe_open(self, mock_run, mock_which):
        from devbase.commands.pkm import icebox
        from typer import Context

        # Mock shutil.which to return a path
        mock_which.return_value = "/usr/bin/code"

        # Create a mock context
        root_path = Path("/tmp/mock_root")
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.obj = {"root": root_path}

        with patch('pathlib.Path.exists', return_value=True):
             # Call icebox with no idea (opens editor)
            icebox(mock_ctx, idea=None)

            # Assert subprocess.run was called
            self.assertTrue(mock_run.called, "subprocess.run should be called when code is available")

            # Get the args
            args, kwargs = mock_run.call_args

            # Check for security
            if kwargs.get('shell') is True:
                self.fail("subprocess.run called with shell=True! Vulnerable to command injection.")

            self.assertIsInstance(args[0], list, "subprocess.run should be called with a list of arguments")
            self.assertEqual(args[0][0], "/usr/bin/code", "First argument should be the resolved path to 'code'")

if __name__ == '__main__':
    unittest.main()
