"""
Security Enforcer - Quota and Path Blocking
============================================
Enforces security policies for AI generation features.

Features:
- Blocked path patterns (config-driven)
- Daily artifact quota tracking (via EventRepository / DuckDB)
- Human approval requirement (stub)
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

from devbase.adapters.storage.event_repository import EventRepository


class SecurityError(Exception):
    """Raised when a security policy is violated."""
    pass


class QuotaExceeded(Exception):
    """Raised when the daily quota is exceeded."""
    pass


@dataclass
class EnforcerConfig:
    """Configuration for security enforcement."""

    max_daily_artifacts: int = 5
    human_approval_required: bool = True
    blocked_paths: list[str] = field(default_factory=lambda: [
        "12_private_vault/",
        "*.env",
        "credentials/",
        "*secret*",
        "*.pem",
        "*.key",
    ])


class SecurityEnforcer:
    """Enforces security policies for AI-generated content.

    Args:
        config: Enforcement configuration (uses defaults if ``None``).
        events: Event repository for quota tracking (instantiated lazily if omitted).

    Usage::

        enforcer = SecurityEnforcer()
        enforcer.enforce(target_path, user_id)  # raises on violation
        enforcer.record_usage(user_id)
    """

    def __init__(
        self,
        config: EnforcerConfig | None = None,
        events: EventRepository | None = None,
    ) -> None:
        self.config = config or EnforcerConfig()
        self._events = events

    @property
    def events(self) -> EventRepository:
        if self._events is None:
            self._events = EventRepository()
        return self._events

    def enforce(self, path: str | Path, user: str) -> None:
        """Enforce security policies for *path*.

        Args:
            path: Target path for AI generation.
            user: User identifier.

        Raises:
            SecurityError: If the path matches a blocked pattern.
            QuotaExceeded: If the daily artifact quota is exceeded.
        """
        path_str = str(path).replace("\\", "/").lower()

        for pattern in self.config.blocked_paths:
            pattern_lower = pattern.lower()
            if (
                fnmatch.fnmatch(path_str, f"*{pattern_lower}*")
                or pattern_lower.rstrip("/") in path_str
            ):
                raise SecurityError(f"Path blocked by security policy: {pattern}")

        current_count = self.events.count_today_by_type("ai_generation", user=user)
        if current_count >= self.config.max_daily_artifacts:
            raise QuotaExceeded(
                f"Daily limit of {self.config.max_daily_artifacts} "
                f"artifacts reached for user '{user}'"
            )

    def record_usage(self, user: str) -> int:
        """Record one artifact generation for *user* and return the new count.

        Args:
            user: User identifier.

        Returns:
            Updated count for today.
        """
        import json as _json
        self.events.log(
            event_type="ai_generation",
            message="Artifact generated",
            metadata=_json.dumps({"user": user}),
        )
        return self.events.count_today_by_type("ai_generation", user=user)

    def get_remaining_quota(self, user: str) -> int:
        """Return the number of artifacts *user* can still generate today."""
        current = self.events.count_today_by_type("ai_generation", user=user)
        return max(0, self.config.max_daily_artifacts - current)

    def is_approval_required(self) -> bool:
        """Check if human approval is required for AI artifacts."""
        return self.config.human_approval_required


def get_enforcer(config: EnforcerConfig | None = None) -> SecurityEnforcer:
    """Return a new ``SecurityEnforcer`` with *config* (or defaults)."""
    return SecurityEnforcer(config)
