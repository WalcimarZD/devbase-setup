
import sys
from pathlib import Path
import pytest

# Ensure local modules/python is importable
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "modules" / "python"))

from filesystem import FileSystem  # noqa: E402
from ui import UI  # noqa: E402
from setup_operations import run_setup_operations  # noqa: E402


def test_setup_operations_creates_structure(tmp_path):
    fs = FileSystem(str(tmp_path))
    ui = UI(no_color=True)
    
    # Mocking devbase.py existence for the copy step
    # We need devbase.py to exist relative to modules/python/setup_operations.py
    # But in test environment, we might run from anywhere.
    # The setup_operations uses __file__ to locate source. 
    # If we run this test, setup_operations.__file__ will point to the real file in d:\devbase-setup...
    # So it will try to find d:\devbase-setup\devbase.py. That file DOES exist.
    # So the copy should work if we target tmp_path as root.
    
    run_setup_operations(fs, ui)
    
    # Check base structure
    ops_root = tmp_path / "30-39_OPERATIONS"
    assert (ops_root / "31_backups").exists()
    assert (ops_root / "35_devbase_cli").exists()
    
    # Check if devbase.py was copied
    assert (ops_root / "35_devbase_cli" / "devbase.py").exists()
