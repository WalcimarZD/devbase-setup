"""
Simple State Manager
====================
Minimal state persistence using JSON, replacing the over-engineered adapter layer.

This module provides direct file-based state management without the complexity
of the Strangler Fig adapter pattern that was never fully implemented.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class StateManager:
    """
    Manages DevBase workspace state via a simple JSON file.
    
    Replaces the previous adapter + legacy pattern with direct pathlib/json usage.
    """
    
    DEFAULT_STATE = {
        "version": "0.0.0",
        "policyVersion": "4.0",
        "installedAt": None,
        "lastUpdate": None,
        "migrations": [],
    }
    
    def __init__(self, root_path: Path):
        """
        Initialize state manager.
        
        Args:
            root_path: Workspace root directory
        """
        if isinstance(root_path, str):
            root_path = Path(root_path)
        self.root = root_path
        self.state_file = root_path / ".devbase_state.json"
        self._state: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load state from disk or initialize defaults."""
        if self.state_file.exists():
            try:
                self._state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._state = self.DEFAULT_STATE.copy()
        else:
            # Create fresh copy to avoid shared mutable state (list)
            self._state = {
                "version": "0.0.0",
                "policyVersion": "4.0",
                "installedAt": None,
                "lastUpdate": None,
                "migrations": [],
            }
    
    def get_state(self) -> Dict[str, Any]:
        """Return current state dictionary."""
        return self._state.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value by key."""
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a state value by key."""
        self._state[key] = value
    
    def save_state(self, new_state: Dict[str, Any]) -> None:
        """Persist state to disk."""
        self._state = new_state
        self.save()
    
    def save(self) -> None:
        """Write current state to disk."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(self._state, indent=2, default=str),
            encoding="utf-8"
        )


def get_state_manager(root_path: Path) -> StateManager:
    """Factory function for StateManager."""
    return StateManager(root_path)
