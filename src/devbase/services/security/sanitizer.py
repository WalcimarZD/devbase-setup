"""
Context Sanitizer - 4-Layer Security
=====================================
Implements the 4-layer sanitization pipeline per TDD v1.2.

Layers:
1. Secret Detection (regex patterns)
2. Path Anonymization (hash + salt)
3. Token Truncation (max_tokens limit)
4. Audit Signature (SHA256 hash only - NEVER raw content)

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Callable


# Secret detection patterns (TDD v1.2 Section 7.2)
# These regex patterns capture both the key identifier AND the secret value
SECRETS_PATTERNS: list[re.Pattern[str]] = [
    # Generic secret patterns: captures key=value or key: value
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+"),
    re.compile(r"sk-[a-zA-Z0-9]{48}"),     # OpenAI API keys
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),    # GitHub Personal Access Tokens
    re.compile(r"AKIA[0-9A-Z]{16}"),       # AWS Access Key IDs
    re.compile(r"gsk_[a-zA-Z0-9]{52}"),    # Groq API keys
    re.compile(r"xox[baprs]-[a-zA-Z0-9-]+"),  # Slack tokens
]


@dataclass
class SecurityConfig:
    """Configuration for security operations."""
    
    secrets_patterns: list[re.Pattern[str]] = field(
        default_factory=lambda: SECRETS_PATTERNS.copy()
    )
    daily_salt: str = field(default_factory=lambda: date.today().isoformat())
    user_id: str = "anonymous"
    max_tokens: int = 2000
    
    def rotate_salt(self) -> None:
        """Rotate the daily salt (call at midnight)."""
        self.daily_salt = date.today().isoformat()


@dataclass
class SanitizedContext:
    """Result of context sanitization."""
    
    content: str
    signature: str
    sanitized_at: datetime = field(default_factory=datetime.now)
    layers_applied: list[str] = field(default_factory=list)


def remove_secrets(content: str, patterns: list[re.Pattern[str]] | None = None) -> str:
    """
    Layer 1: Remove secrets from content.
    
    Replaces matched patterns with [REDACTED].
    
    Args:
        content: Raw content string
        patterns: Regex patterns to match (defaults to SECRETS_PATTERNS)
        
    Returns:
        Content with secrets redacted
    """
    if patterns is None:
        patterns = SECRETS_PATTERNS
    
    result = content
    for pattern in patterns:
        result = pattern.sub("[REDACTED]", result)
    
    return result


def anonymize_paths(content: str, salt: str) -> str:
    """
    Layer 2: Anonymize file paths.
    
    Replaces absolute paths with hashed versions to prevent
    leaking directory structure information.
    
    Args:
        content: Content string
        salt: Daily salt for consistent hashing
        
    Returns:
        Content with paths anonymized
    """
    # Pattern for Windows and Unix absolute paths
    path_pattern = re.compile(
        r"(?:[A-Za-z]:\\[\w\\.-]+|/(?:home|Users|var|tmp|opt)/[\w/.-]+)"
    )
    
    def hash_path(match: re.Match[str]) -> str:
        path = match.group(0)

        # Use appropriate Path class based on path format
        # This ensures correct parsing on any OS (e.g. Windows paths on Linux)
        if re.match(r"[A-Za-z]:\\", path):
            p = PureWindowsPath(path)
        else:
            p = PurePosixPath(path)

        parts = p.parts
        if len(parts) > 1:
            # Hash directory components
            dir_hash = hashlib.sha256(
                (salt + str(p.parent)).encode()
            ).hexdigest()[:8]
            return f"[PATH:{dir_hash}]/{parts[-1]}"
        return path
    
    return path_pattern.sub(hash_path, content)


def truncate_tokens(content: str, max_tokens: int = 2000) -> str:
    """
    Layer 3: Truncate content to max token limit.
    
    Uses simple word-based approximation (1 token ≈ 0.75 words).
    
    Args:
        content: Content string
        max_tokens: Maximum token count
        
    Returns:
        Truncated content
    """
    # Approximate: 1 token ≈ 4 characters (conservative)
    max_chars = max_tokens * 4
    
    if len(content) <= max_chars:
        return content
    
    truncated = content[:max_chars]
    # Try to truncate at word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    
    return truncated + "\n[TRUNCATED]"


def audit_log(
    signature: str,
    timestamp: datetime,
    user_hash: int,
    log_func: Callable[[str], None] | None = None
) -> None:
    """
    Layer 4: Audit logging (hash only, NEVER raw content).
    
    This is a critical security requirement - raw content must
    never be logged for audit purposes.
    
    Args:
        signature: SHA256 hash of sanitized content
        timestamp: When sanitization occurred
        user_hash: Hashed user identifier
        log_func: Optional custom log function
    """
    log_entry = f"AUDIT|{timestamp.isoformat()}|user:{user_hash}|sig:{signature[:16]}"
    
    if log_func:
        log_func(log_entry)
    # Default: silent (audit logs go to DuckDB via adapter)


def sanitize_context(raw: str, config: SecurityConfig | None = None) -> SanitizedContext:
    """
    Full 4-layer sanitization pipeline.
    
    Applies all security layers in order:
    1. Secret removal
    2. Path anonymization
    3. Token truncation
    4. Audit signature generation
    
    CRITICAL: Never logs or stores raw content.
    
    Args:
        raw: Raw content to sanitize
        config: Security configuration (uses defaults if None)
        
    Returns:
        SanitizedContext with sanitized content and signature
    """
    if config is None:
        config = SecurityConfig()
    
    layers_applied = []
    
    # Layer 1: Secret detection and removal
    step1 = remove_secrets(raw, config.secrets_patterns)
    if step1 != raw:
        layers_applied.append("secrets_removed")
    
    # Layer 2: Path anonymization
    step2 = anonymize_paths(step1, salt=config.daily_salt)
    if step2 != step1:
        layers_applied.append("paths_anonymized")
    
    # Layer 3: Token truncation
    step3 = truncate_tokens(step2, max_tokens=config.max_tokens)
    if step3 != step2:
        layers_applied.append("truncated")
    
    # Layer 4: Signature generation
    signature = hashlib.sha256(step3.encode()).hexdigest()
    layers_applied.append("signature_generated")
    
    # Audit log (hash only, NEVER raw)
    audit_log(signature, datetime.now(), hash(config.user_id))
    
    return SanitizedContext(
        content=step3,
        signature=signature,
        layers_applied=layers_applied,
    )
