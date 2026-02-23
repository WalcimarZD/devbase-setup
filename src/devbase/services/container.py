from __future__ import annotations
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from devbase.utils.filesystem import FileSystem
    from devbase.utils.state import StateManager
    from devbase.utils.telemetry import TelemetryService
    from devbase.ai.service import AIService

class ServiceContainer:
    """
    Workspace-scoped Dependency Injection (DI) Container.
    
    Provides lazy-initialized, cached instances of core services. 
    Uses @cached_property to ensure thread-safe, singleton-per-workspace behavior.
    """

    def __init__(self, root: Path) -> None:
        """
        Initialize the container for a specific workspace.
        @param root: Canonical Path to the Johnny.Decimal workspace root.
        """
        self.root = root

    @cached_property
    def filesystem(self) -> FileSystem:
        """Port for atomic filesystem operations."""
        from devbase.utils.filesystem import get_filesystem
        return get_filesystem(str(self.root))

    @cached_property
    def state_manager(self) -> StateManager:
        """State manager for workspace metadata."""
        from devbase.utils.state import get_state_manager
        return get_state_manager(self.root)

    @cached_property
    def telemetry(self) -> TelemetryService:
        """
        OLAP Telemetry provider using DuckDB.
        @requires: devbase[db] extra.
        """
        from devbase.utils.telemetry import get_telemetry
        return get_telemetry(self.root)

    @cached_property
    def ai(self) -> AIService:
        """
        Orchestrator for LLM-powered workspace features.
        @requires: devbase[ai] extra.
        """
        from devbase.ai.service import AIService
        from devbase.ai.providers.groq import GroqProvider
        return AIService(GroqProvider())
