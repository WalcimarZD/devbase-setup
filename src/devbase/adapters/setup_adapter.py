"""
Setup Functions Anti-Corruption Layer Adapter
==============================================
Factory functions that route to legacy or modern setup implementations
based on configuration flags.

USAGE:
    from devbase.adapters.setup_adapter import (
        run_setup_core,
        run_setup_code,
        run_setup_ai,
        run_setup_operations,
        run_setup_pkm,
    )
    
    run_setup_core(fs, state)
"""
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:
    from devbase.adapters.filesystem_adapter import IFileSystem
    from devbase.adapters.state_adapter import IStateManager


def _get_setup_function(
    legacy_module: str,
    legacy_func: str,
    config_key: str,
) -> Callable[..., Any]:
    """
    Internal helper to create setup function wrapper.
    
    Args:
        legacy_module: Module path in _deprecated package
        legacy_func: Function name in that module
        config_key: Config key to check for legacy/modern routing
        
    Returns:
        Callable: The appropriate setup function
    """
    from devbase.utils.config import get_config
    
    config = get_config()
    use_legacy = config.get(config_key, True)
    log_calls = config.get("migration.log_legacy_calls", False)
    
    if use_legacy:
        import importlib
        module = importlib.import_module(legacy_module)
        func = getattr(module, legacy_func)
        
        if log_calls:
            import logging
            logger = logging.getLogger("devbase.deprecated")
            logger.warning(
                f"DEPRECATED: Using legacy {legacy_module}.{legacy_func}(). "
                f"Set {config_key}=false to use modern implementation."
            )
        
        return func
    else:
        # TODO: Implement modern setup functions when ready
        import warnings
        warnings.warn(
            f"Modern {legacy_func} not yet implemented. Falling back to legacy.",
            FutureWarning,
            stacklevel=3
        )
        import importlib
        module = importlib.import_module(legacy_module)
        return getattr(module, legacy_func)


def run_setup_core(fs: "IFileSystem", state: "IStateManager") -> None:
    """
    Run core workspace setup (folder structure, config files).
    
    Routes to legacy or modern implementation based on config.
    """
    func = _get_setup_function(
        "devbase._deprecated.setup_core",
        "run_setup_core",
        "migration.use_legacy_setup_core",
    )
    return func(fs, state)


def run_setup_code(fs: "IFileSystem", state: "IStateManager") -> None:
    """
    Run code environment setup (packages, development tools).
    
    Routes to legacy or modern implementation based on config.
    """
    func = _get_setup_function(
        "devbase._deprecated.setup_code",
        "run_setup_code",
        "migration.use_legacy_setup_code",
    )
    return func(fs, state)


def run_setup_ai(fs: "IFileSystem", state: "IStateManager") -> None:
    """
    Run AI tools setup (prompts, agents, configurations).
    
    Routes to legacy or modern implementation based on config.
    """
    func = _get_setup_function(
        "devbase._deprecated.setup_ai",
        "run_setup_ai",
        "migration.use_legacy_setup_ai",
    )
    return func(fs, state)


def run_setup_operations(fs: "IFileSystem", state: "IStateManager") -> None:
    """
    Run operations setup (backup, monitoring, automation).
    
    Routes to legacy or modern implementation based on config.
    """
    func = _get_setup_function(
        "devbase._deprecated.setup_operations",
        "run_setup_operations",
        "migration.use_legacy_setup_ops",
    )
    return func(fs, state)


def run_setup_pkm(fs: "IFileSystem", state: "IStateManager") -> None:
    """
    Run PKM setup (knowledge management, templates).
    
    Routes to legacy or modern implementation based on config.
    """
    func = _get_setup_function(
        "devbase._deprecated.setup_pkm",
        "run_setup_pkm",
        "migration.use_legacy_setup_pkm",
    )
    return func(fs, state)
