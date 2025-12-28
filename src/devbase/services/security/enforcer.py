"""
Security Enforcer - Quota and Path Blocking
============================================
Enforces security policies for AI generation features.

Features:
- Blocked path patterns (config-driven)
- Daily artifact quota tracking (Persistent in DuckDB)
- Human approval requirement (stub)

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from devbase.adapters.storage import duckdb_adapter


class SecurityError(Exception):
    """Raised when a security policy is violated."""
    pass


class QuotaExceeded(Exception):
    """Raised when daily quota is exceeded."""
    pass


@dataclass
class QuotaTracker:
    """
    Tracks daily AI generation quotas using DuckDB.
    
    Persistence is handled by the 'events' table in DuckDB.
    """
    
    def get_count(self, user: str) -> int:
        """
        Get today's artifact count for a user from DuckDB.

        Queries the events table for 'ai_generation' events created today
        by the specified user.
        """
        conn = duckdb_adapter.get_connection()

        # Query for events today
        # Use DuckDB's date_trunc or casting to date
        query = """
            SELECT COUNT(*)
            FROM events
            WHERE event_type = 'ai_generation'
              AND timestamp::DATE = current_date()
        """
        
        # If user is specified, check metadata.
        # Note: We assume metadata contains JSON with 'user' field.
        # Since metadata is TEXT, we use json_extract.
        if user:
             # This assumes metadata is valid JSON. The schema check enforces it or NULL.
             # We need to handle potential NULLs safely if not all events have metadata.
             # DuckDB json_extract returns NULL if path doesn't exist or JSON is invalid.
             # However, for this to work robustly, we'll fetch all today's events and filter in SQL if possible,
             # or filter in Python if SQL json extraction is tricky with simple string matching.
             # DuckDB's JSON extension is powerful.
             query += " AND json_extract_string(metadata, '$.user') = ?"
             result = conn.execute(query, [user]).fetchone()
        else:
             result = conn.execute(query).fetchone()

        return result[0] if result else 0
    
    def record_usage(self, user: str) -> int:
        """
        Record an artifact generation event in DuckDB.

        Args:
            user: User identifier

        Returns:
            New count for today
        """
        metadata = json.dumps({"user": user})
        duckdb_adapter.log_event(
            event_type="ai_generation",
            message="Artifact generated",
            metadata=metadata
        )
        return self.get_count(user)


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
            enforcer.record_usage(user_id)
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
        return self.tracker.record_usage(user)
    
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
