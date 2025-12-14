
import sys
from pathlib import Path
import pytest

# Ensure local modules/python is importable
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "modules" / "python"))

from filesystem import FileSystem  # noqa: E402
from ui import UI  # noqa: E402
from setup_pkm import run_setup_pkm  # noqa: E402


def test_setup_pkm_creates_structure(tmp_path):
    fs = FileSystem(str(tmp_path))
    ui = UI(no_color=True)
    
    run_setup_pkm(fs, ui)
    
    # Check base structure
    assert (tmp_path / "10-19_KNOWLEDGE" / "11_public_garden").exists()
    assert (tmp_path / "10-19_KNOWLEDGE" / "12_private_vault" / "credentials").exists()
    
    # Check references
    assert (tmp_path / "10-19_KNOWLEDGE" / "15_references" / "patterns").exists()

def test_setup_pkm_replacements(tmp_path, monkeypatch):
    # Integration test for replacement logic with fake template
    from datetime import datetime
    
    # Setup fake templates
    fake_root = tmp_path / "fake_templates" / "pkm"
    fake_root.mkdir(parents=True)
    
    template_content = "Year: {{YEAR}}, Week: {{WEEK_NUMBER}}"
    (fake_root / "test_note.md.template").write_text(template_content, encoding="utf-8")
    
    # Filename replacement test: {{YEAR}}-log.md.template
    (fake_root / "{{YEAR}}-log.md.template").write_text("Content", encoding="utf-8")
    
    # Mock the templates location in setup_pkm
    # Since we can't easily mock internal variables of the module without refactoring,
    # let's call process_templates directly to test ONLY the replacement logic 
    # instead of full run_setup_pkm which hardcodes the path.
    
    from template_utils import process_templates
    
    fs = FileSystem(str(tmp_path))
    ui = UI(no_color=True)
    
    now = datetime.now()
    replacements = {
        "{{YEAR}}": now.strftime("%Y"),
        "{{WEEK_NUMBER}}": now.strftime("%V"),
    }
    
    process_templates(fs, ui, fake_root, base_dest_path="10-19_KNOWLEDGE", extra_replacements=replacements)
    
    # Verify content replacement
    dest_file = tmp_path / "10-19_KNOWLEDGE" / "test_note.md"
    assert dest_file.exists()
    content = dest_file.read_text(encoding="utf-8")
    assert f"Year: {now.strftime('%Y')}" in content
    
    # Verify filename replacement
    year_log = tmp_path / "10-19_KNOWLEDGE" / f"{now.strftime('%Y')}-log.md"
    assert year_log.exists()
