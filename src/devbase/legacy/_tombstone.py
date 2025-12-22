"""
Deprecation Infrastructure for DevBase Legacy Code
===================================================
Provides decorators and utilities for marking legacy code as deprecated
with proper logging and warning emission.

USAGE:
    from devbase._deprecated._tombstone import deprecated
    
    @deprecated(replacement="adapters.filesystem_adapter.get_filesystem")
    def old_function():
        ...
"""
import logging
import warnings
from functools import wraps
from typing import Callable, Optional, TypeVar, Any

logger = logging.getLogger("devbase.deprecated")

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(
    replacement: Optional[str] = None,
    removal_version: str = "5.0.0",
    emit_warning: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to mark functions/methods as deprecated with logging.
    
    When a deprecated function is called:
    1. A warning is logged to devbase.deprecated logger
    2. A DeprecationWarning is emitted (visible with -W flag)
    3. The original function executes normally
    
    Args:
        replacement: Suggested replacement (e.g., "adapters.filesystem_adapter")
        removal_version: Version when this will be removed (default: 5.0.0)
        emit_warning: Whether to emit Python warning (default: True)
        
    Returns:
        Decorated function that logs deprecation on each call
        
    Example:
        @deprecated(replacement="FileSystemV2.ensure_dir")
        def ensure_dir(self, path: str) -> Path:
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build deprecation message
            full_name = f"{func.__module__}.{func.__qualname__}"
            msg = f"DEPRECATED: {full_name}() is deprecated"
            
            if replacement:
                msg += f". Use {replacement} instead"
            
            msg += f". Will be removed in v{removal_version}"
            
            # Log warning (always, visible in verbose mode)
            logger.warning(msg)
            
            # Emit Python warning (visible with -W flag)
            if emit_warning:
                warnings.warn(msg, DeprecationWarning, stacklevel=2)
            
            # Execute original function
            return func(*args, **kwargs)
        
        # Mark as deprecated for introspection
        wrapper.__deprecated__ = True  # type: ignore
        wrapper.__deprecated_info__ = {  # type: ignore
            "replacement": replacement,
            "removal_version": removal_version,
        }
        
        return wrapper  # type: ignore
    
    return decorator


def is_deprecated(func: Callable[..., Any]) -> bool:
    """
    Check if a function is marked as deprecated.
    
    Args:
        func: Function to check
        
    Returns:
        True if function has @deprecated decorator
        
    Example:
        if is_deprecated(some_function):
            print("This function is deprecated!")
    """
    return getattr(func, "__deprecated__", False)


def get_deprecation_info(func: Callable[..., Any]) -> Optional[dict]:
    """
    Get deprecation metadata from a deprecated function.
    
    Args:
        func: Function to inspect
        
    Returns:
        Dict with 'replacement' and 'removal_version', or None
    """
    return getattr(func, "__deprecated_info__", None)
