
import sys
from unittest.mock import MagicMock, patch
import pytest
from devbase.commands.debug import run_unit_tests, DebugReport

def test_run_unit_tests_missing_pytest():
    """
    Verify that run_unit_tests handles the absence of pytest gracefully.
    It should log a warning and set the result to FAILED with a helpful message.
    """
    # Create a mock report object
    mock_report = MagicMock(spec=DebugReport)

    # We need to simulate that 'pytest' cannot be imported.
    # We use patch.dict on sys.modules to remove pytest if it exists,
    # and a side_effect on builtins.__import__ (or simpler, just ensure import fails).

    # However, since the function does "import pytest", we can mock `builtins.__import__`
    # but that is tricky because it affects everything.
    # A better approach for testing "import X" failure is to use `sys.modules` manipulation
    # combined with a custom finder/loader or just patching the specific module if it was already imported.

    # Since `pytest` is likely already imported by the test runner itself,
    # we need to ensure the import statement inside the function fails.

    # Strategy: Patch `builtins.__import__` is risky.
    # Strategy: Use `unittest.mock.patch.dict(sys.modules, {'pytest': None})`
    # This might cause `import pytest` to raise ImportError depending on python version,
    # but often it just returns None.

    # Reliable Strategy:
    # 1. Hide real pytest from sys.modules
    # 2. Use a custom Importer that raises ImportError for 'pytest'

    with patch.dict(sys.modules):
        # Remove pytest from sys.modules so it tries to reload
        if 'pytest' in sys.modules:
            del sys.modules['pytest']

        # Mock the import mechanism to fail for 'pytest'
        # We can use a side effect on builtins.__import__ but limit it to 'pytest'
        import builtins
        original_import = builtins.__import__

        def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'pytest':
                raise ImportError("No module named 'pytest'")
            return original_import(name, globals, locals, fromlist, level)

        with patch('builtins.__import__', side_effect=mock_import):
            run_unit_tests(mock_report)

    # Assertions
    # 1. Check if warning was logged
    mock_report.log.assert_any_call("pytest not found. Skipping unit tests.", level="WARNING")

    # 2. Check result
    mock_report.set_unit_test_result.assert_called_with(
        -1,
        "pytest not installed. Install dev dependencies to run unit tests."
    )
