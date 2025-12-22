"""
Tests for workspace detection utility.
"""
import os
from pathlib import Path
import tempfile
import json

import pytest

from devbase.utils.workspace import (
    detect_workspace_root,
    is_valid_workspace,
    get_workspace_areas,
    get_semantic_locations,
)


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary DevBase workspace for testing."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    
    # Create state file
    state_file = workspace / ".devbase_state.json"
    state_file.write_text(json.dumps({
        "version": "4.0.0",
        "installedAt": "2025-01-01T00:00:00",
        "lastUpdate": "2025-01-01T00:00:00",
        "migrations": [],
    }))
    
    # Create basic structure
    areas = [
        "00-09_SYSTEM",
        "10-19_KNOWLEDGE",
        "20-29_CODE",
        "30-39_OPERATIONS",
    ]
    for area in areas:
        (workspace / area).mkdir()
    
    return workspace


def test_is_valid_workspace(temp_workspace):
    """Test workspace validation."""
    assert is_valid_workspace(temp_workspace) is True
    assert is_valid_workspace(temp_workspace / "nonexistent") is False


def test_detect_workspace_from_child_dir(temp_workspace, monkeypatch):
    """Test detection from child directory."""
    child_dir = temp_workspace / "20-29_CODE"
    monkeypatch.chdir(child_dir)
    
    detected = detect_workspace_root()
    assert detected == temp_workspace


def test_detect_workspace_from_env(temp_workspace, monkeypatch):
    """Test detection from environment variable."""
    monkeypatch.setenv("DEVBASE_ROOT", str(temp_workspace))
    monkeypatch.chdir(tempfile.gettempdir())
    
    detected = detect_workspace_root()
    assert detected == temp_workspace


def test_get_workspace_areas(temp_workspace):
    """Test getting workspace areas."""
    areas = get_workspace_areas(temp_workspace)
    
    assert "system" in areas
    assert "knowledge" in areas
    assert "code" in areas
    assert areas["system"] == temp_workspace / "00-09_SYSTEM"


def test_get_semantic_locations(temp_workspace):
    """Test semantic location shortcuts."""
    locations = get_semantic_locations(temp_workspace)
    
    assert "code" in locations
    assert "vault" in locations
    assert locations["code"] == temp_workspace / "20-29_CODE" / "21_monorepo_apps"
