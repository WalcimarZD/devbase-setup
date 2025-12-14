
import sys
from pathlib import Path
import pytest

# Ensure local modules/python is importable
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "modules" / "python"))

from filesystem import FileSystem  # noqa: E402
from ui import UI  # noqa: E402
from setup_ai import run_setup_ai  # noqa: E402


def test_setup_ai_creates_structure(tmp_path):
    fs = FileSystem(str(tmp_path))
    ui = UI(no_color=True)
    
    run_setup_ai(fs, ui)
    
    # Check base structure
    ai_root = tmp_path / "30-39_OPERATIONS" / "30_ai"
    assert ai_root.exists()
    assert (ai_root / "31_ai_local" / "context").exists()
    assert (ai_root / "32_ai_models" / "models").exists()
    assert (ai_root / "33_ai_config" / "security").exists()
