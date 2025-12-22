
import json
from pathlib import Path
import pytest

from devbase._deprecated.state import StateManager


def test_get_initial_state(tmp_path):
    mgr = StateManager(tmp_path)
    state = mgr.get_state()
    assert state["version"] == "0.0.0"
    assert state["migrations"] == []


def test_save_and_get_state(tmp_path):
    mgr = StateManager(tmp_path)
    
    state = mgr.get_initial_state()
    state["version"] = "1.0.0"
    state["modules"] = ["core", "pkm"]
    
    mgr.save_state(state)
    
    # Reload
    new_mgr = StateManager(tmp_path)
    loaded = new_mgr.get_state()
    
    assert loaded["version"] == "1.0.0"
    assert "core" in loaded["modules"]
    assert loaded["lastUpdate"] is not None  # Auto-filled


def test_save_state_creates_file(tmp_path):
    mgr = StateManager(tmp_path)
    mgr.save_state({"test": "data"})
    
    state_file = tmp_path / ".devbase_state.json"
    assert state_file.exists()
    
    content = json.loads(state_file.read_text(encoding="utf-8"))
    assert content["test"] == "data"
