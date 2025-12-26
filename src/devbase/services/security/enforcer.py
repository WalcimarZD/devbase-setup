"""
Security Enforcer - Quota and Path Blocking
============================================
Enforces security policies for AI generation features.

Features:
- Blocked path patterns (config-driven)
- Daily artifact quota tracking
- Human approval requirement (stub)

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


class SecurityError(Exception):
    """Raised when a security policy is violated."""
    pass


class QuotaExceeded(Exception):
    """Raised when daily quota is exceeded."""
    pass


@dataclass
class QuotaTracker:
    """Tracks daily AI generation quotas."""
    
    _counts: dict[str, dict[str, int]] = field(default_factory=dict)
    
    def _get_today_key(self) -> str:
        return date.today().isoformat()
    
    def get_count(self, user: str) -> int:
        """Get today's artifact count for a user."""
        today = self._get_today_key()
        if today not in self._counts:
            self._counts[today] = {}
        return self._counts[today].get(user, 0)
    
    def increment(self, user: str) -> int:
        """Increment and return new count for today."""
        today = self._get_today_key()
        if today not in self._counts:
            # Clean up old dates
            self._counts = {today: {}}
        
        current = self._counts[today].get(user, 0)
        self._counts[today][user] = current + 1
        return current + 1
    
    def reset(self, user: str) -> None:
        """Reset quota for a user (for testing)."""
        today = self._get_today_key()
        if today in self._counts:
            self._counts[today][user] = 0


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
    """
    Enforces security policies for AI-generated content.
    
    Usage:
        enforcer = SecurityEnforcer(config)
        try:
            enforcer.enforce(target_path, user_id)
            # Proceed with AI generation
        except SecurityError as e:
            console.print(f"[red]Blocked: {e}[/red]")
        except QuotaExceeded as e:
            console.print(f"[yellow]Quota exceeded: {e}[/yellow]")
    """
    
    def __init__(self, config: EnforcerConfig | None = None):
        """
        Initialize enforcer.
        
        Args:
            config: Enforcement configuration (uses defaults if None)
        """
        self.config = config or EnforcerConfig()
        self.tracker = QuotaTracker()
    
    def enforce(self, path: str | Path, user: str) -> None:
        """
        Enforce security policies for a path.
        
        Args:
            path: Target path for AI generation
            user: User identifier
            
        Raises:
            SecurityError: If path matches a blocked pattern
            QuotaExceeded: If daily quota is exceeded
        """
        path_str = str(path).replace("\\", "/").lower()
        
        # Check blocked paths
        for pattern in self.config.blocked_paths:
            pattern_lower = pattern.lower()
            
            # Handle both glob patterns and substring matches
            if fnmatch.fnmatch(path_str, f"*{pattern_lower}*"):
                raise SecurityError(
                    f"Path blocked by security policy: {pattern}"
                )
            
            # Also check if pattern appears as a path segment
            if pattern_lower.rstrip("/") in path_str:
                raise SecurityError(
                    f"Path blocked by security policy: {pattern}"
                )
        
        # Check quota
        current_count = self.tracker.get_count(user)
        if current_count >= self.config.max_daily_artifacts:
            raise QuotaExceeded(
                f"Daily limit of {self.config.max_daily_artifacts} "
                f"artifacts reached for user '{user}'"
            )
    
    def record_usage(self, user: str) -> int:
        """
        Record an artifact generation (call after successful generation).
        
        Args:
            user: User identifier
            
        Returns:
            New count for today
        """
        return self.tracker.increment(user)
    
    def get_remaining_quota(self, user: str) -> int:
        """
        Get remaining quota for today.
        
        Args:
            user: User identifier
            
        Returns:
            Number of artifacts remaining
        """
        current = self.tracker.get_count(user)
        return max(0, self.config.max_daily_artifacts - current)
    
    def is_approval_required(self) -> bool:
        """Check if human approval is required for AI artifacts."""
        return self.config.human_approval_required


# Module-level singleton
_enforcer: SecurityEnforcer | None = None


def get_enforcer(config: EnforcerConfig | None = None) -> SecurityEnforcer:
    """
    Get or create the singleton SecurityEnforcer.
    
    Args:
        config: Optional config (only used on first call)
        
    Returns:
        SecurityEnforcer instance
    """
    global _enforcer
    
    if _enforcer is None:
        _enforcer = SecurityEnforcer(config)
    
    return _enforcer
