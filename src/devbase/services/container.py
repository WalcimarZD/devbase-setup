"""
Service Container
==================
Lazy-initialized, workspace-scoped service registry.

Caches service instances per workspace root to avoid repeated
factory calls across commands.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Workspace-scoped service container with lazy initialization.

    Each property creates its service on first access and caches it.
    Services that depend on optional extras fail gracefully with hints.

    Usage::

        container = ServiceContainer(workspace_root)
        container.telemetry  # lazy-created on first access
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self._cache: dict[str, Any] = {}

    def _get_or_create(self, key: str, factory: Any) -> Any:
        """Get a cached service or create it via factory."""
        if key not in self._cache:
            try:
                self._cache[key] = factory()
            except ImportError as e:
                logger.warning(f"Service '{key}' unavailable: {e}")
                raise
        return self._cache[key]

    @property
    def filesystem(self) -> Any:
        """Filesystem adapter for the workspace."""
        def _factory() -> Any:
            from devbase.utils.filesystem import get_filesystem
            return get_filesystem(str(self.root))
        return self._get_or_create("filesystem", _factory)

    @property
    def state_manager(self) -> Any:
        """State manager for workspace metadata."""
        def _factory() -> Any:
            from devbase.utils.state import get_state_manager
            return get_state_manager(self.root)
        return self._get_or_create("state_manager", _factory)

    @property
    def telemetry(self) -> Any:
        """Telemetry tracker (requires db extra)."""
        def _factory() -> Any:
            from devbase.utils.telemetry import get_telemetry
            return get_telemetry(self.root)
        return self._get_or_create("telemetry", _factory)
