
from pathlib import Path
import pytest

from devbase._deprecated.filesystem import FileSystem
from devbase._deprecated.ui import UI
from devbase._deprecated.setup_code import run_setup_code


def test_setup_code_creates_structure(tmp_path):
    fs = FileSystem(str(tmp_path))
    ui = UI(no_color=True)
    
    run_setup_code(fs, ui)
    
    # Check base structure
    assert (tmp_path / "20-29_CODE" / "21_monorepo_apps").exists()
    assert (tmp_path / "20-29_CODE" / "22_monorepo_packages" / "shared-types").exists()
    
    # Check Clean Arch structure
    template_root = tmp_path / "20-29_CODE" / "__template-clean-arch"
    assert (template_root / "src/domain/entities").exists()
    assert (template_root / "src/infrastructure/persistence/repositories").exists()
