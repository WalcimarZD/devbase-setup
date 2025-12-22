"""
StateManager Anti-Corruption Layer Adapter
===========================================
Factory function that routes to legacy or modern StateManager implementation
based on configuration flags.

USAGE:
    from devbase.adapters.state_adapter import get_state_manager
    
    state = get_state_manager("/path/to/workspace")
    state.save()
"""
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from devbase._deprecated.state import StateManager


class IStateManager(Protocol):
    """
    Interface contract for state management operations.
    
    All implementations must satisfy this protocol.
    """
    
    state_file: Path
    state: Dict[str, Any]
    
    def load(self) -> Dict[str, Any]:
        """Load state from persistent storage."""
        ...
    
    def save(self) -> None:
        """Persist current state to storage."""
        ...
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value by key."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set state value by key."""
        ...


def get_state_manager(root_path: str) -> IStateManager:
    """
    Factory function that returns the appropriate StateManager implementation.
    
    Args:
        root_path: Path to workspace root directory
        
    Returns:
        IStateManager: Implementation based on config flags
    """
    from devbase.utils.config import get_config
    
    config = get_config()
    use_legacy = config.get("migration.use_legacy_state", True)
    log_calls = config.get("migration.log_legacy_calls", False)
    
    if use_legacy:
        from devbase._deprecated.state import StateManager
        
        if log_calls:
            import logging
            logger = logging.getLogger("devbase.deprecated")
            logger.warning(
                "DEPRECATED: Using legacy StateManager. "
                "Set migration.use_legacy_state=false to use modern implementation."
            )
        
        return StateManager(root_path)
    else:
        # TODO: Implement modern StateManager when ready
        import warnings
        warnings.warn(
            "Modern StateManager not yet implemented. Falling back to legacy.",
            FutureWarning,
            stacklevel=2
        )
        from devbase._deprecated.state import StateManager
        return StateManager(root_path)
