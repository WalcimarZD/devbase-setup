"""
Configuration System
====================
Manages user configuration from devbase.toml file.
"""
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for Python 3.8-3.10


class Config:
    """DevBase configuration manager."""

    DEFAULT_CONFIG = {
        "workspace": {
            "root": None,  # Auto-detected
            "auto_detect": True,
        },
        "behavior": {
            "expert_mode": False,
            "color_output": True,
        },
        "telemetry": {
            "enabled": True,
            "auto_track_commits": False,
        },
        "templates": {
            "default_template": "clean-arch",
        },
        "aliases": {},
        # Migration feature flags (Strangler Fig pattern)
        # Set to False to use modern implementations when available
        "migration": {
            # Module-specific flags
            "use_legacy_filesystem": True,      # FileSystem class
            "use_legacy_state": True,           # StateManager class
            "use_legacy_setup_core": True,      # run_setup_core()
            "use_legacy_setup_code": True,      # run_setup_code()
            "use_legacy_setup_ai": True,        # run_setup_ai()
            "use_legacy_setup_ops": True,       # run_setup_operations()
            "use_legacy_setup_pkm": True,       # run_setup_pkm()
            "use_legacy_knowledge": True,       # KnowledgeDB/Graph
            # Master switch (when False, all legacy is disabled)
            "legacy_enabled": True,
            # Debugging (logs warning on each legacy call)
            "log_legacy_calls": False,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to devbase.toml (default: ~/.devbase/config.toml)
        """
        if config_path is None:
            config_path = Path.home() / ".devbase" / "config.toml"

        self.config_path = config_path
        self._config = self.DEFAULT_CONFIG.copy()

        # Load if exists
        if self.config_path.exists():
            self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, "rb") as f:
                user_config = tomllib.load(f)

            # Merge with defaults
            self._merge_config(user_config)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Deep merge user config with defaults."""
        for section, values in user_config.items():
            if section in self._config and isinstance(values, dict):
                self._config[section].update(values)
            else:
                self._config[section] = values

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Example:
            config.get("behavior.expert_mode")  # → False
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Example:
            config.set("behavior.expert_mode", True)
        """
        keys = key.split(".")
        target = self._config

        # Navigate to parent
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set value
        target[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write TOML
        import toml
        with open(self.config_path, "w") as f:
            toml.dump(self._config, f)

    @property
    def expert_mode(self) -> bool:
        """Quick access to expert mode setting."""
        return self.get("behavior.expert_mode", False)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
