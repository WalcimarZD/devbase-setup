"""
DevBase Adapters Package (Anti-Corruption Layer)
=================================================
Factory functions that route between legacy and modern implementations
based on configuration flags. This is the ONLY entry point for operations
that have both legacy and modern implementations.

USAGE:
    from devbase.adapters.filesystem_adapter import get_filesystem
    fs = get_filesystem(root_path)  # Returns appropriate implementation

MIGRATION GUIDE:
    1. Replace direct imports from devbase._deprecated with adapter imports
    2. Use factory functions instead of direct class instantiation
    3. Toggle implementations via config.toml migration flags
"""
