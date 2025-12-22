
from pathlib import Path
import pytest

from devbase._deprecated.filesystem import FileSystem
from devbase._deprecated.ui import UI
from devbase._deprecated.setup_ai import run_setup_ai


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
