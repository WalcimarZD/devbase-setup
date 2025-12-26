"""
Tests for Security Sanitizer
=============================
Verifies 4-layer sanitization pipeline.
"""
import pytest

from devbase.services.security.sanitizer import (
    sanitize_context,
    remove_secrets,
    anonymize_paths,
    truncate_tokens,
    SECRETS_PATTERNS,
    SecurityConfig,
)


class TestSecretRemoval:
    """Tests for Layer 1: Secret detection."""
    
    def test_removes_api_key_pattern(self):
        """Verify API keys are removed."""
        content = "My api_key: supersecret123"
        result = remove_secrets(content)
        assert "supersecret" not in result
        assert "[REDACTED]" in result
    
    def test_removes_openai_key(self):
        """Verify OpenAI API keys are removed."""
        content = "OPENAI_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890123456789012"
        result = remove_secrets(content)
        assert "sk-" not in result
        assert "[REDACTED]" in result
    
    def test_removes_github_token(self):
        """Verify GitHub PATs are removed."""
        content = "token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = remove_secrets(content)
        assert "ghp_" not in result
        assert "[REDACTED]" in result
    
    def test_removes_aws_key(self):
        """Verify AWS keys are removed."""
        content = "AWS_KEY=AKIAIOSFODNN7EXAMPLE"
        result = remove_secrets(content)
        assert "AKIA" not in result
        assert "[REDACTED]" in result
    
    def test_preserves_safe_content(self):
        """Verify non-secret content is preserved."""
        content = "This is a normal message without secrets."
        result = remove_secrets(content)
        assert result == content


class TestPathAnonymization:
    """Tests for Layer 2: Path anonymization."""
    
    def test_anonymizes_windows_path(self):
        """Verify Windows paths are anonymized."""
        content = r"File at C:\Users\john\Documents\secret.txt"
        result = anonymize_paths(content, salt="test-salt")
        assert "john" not in result
        assert "secret.txt" in result  # Filename preserved
        assert "[PATH:" in result
    
    def test_anonymizes_unix_path(self):
        """Verify Unix paths are anonymized."""
        content = "Config at /home/user/config/settings.json"
        result = anonymize_paths(content, salt="test-salt")
        assert "user" not in result
        assert "settings.json" in result  # Filename preserved
    
    def test_consistent_with_same_salt(self):
        """Verify same salt produces same hash."""
        content = "/home/user/file.txt"
        result1 = anonymize_paths(content, salt="same-salt")
        result2 = anonymize_paths(content, salt="same-salt")
        assert result1 == result2


class TestTokenTruncation:
    """Tests for Layer 3: Token truncation."""
    
    def test_truncates_long_content(self):
        """Verify long content is truncated."""
        content = "x" * 10000
        result = truncate_tokens(content, max_tokens=100)
        assert len(result) < len(content)
        assert "[TRUNCATED]" in result
    
    def test_preserves_short_content(self):
        """Verify short content is not truncated."""
        content = "Short message"
        result = truncate_tokens(content, max_tokens=100)
        assert result == content
        assert "[TRUNCATED]" not in result


class TestSanitizeContext:
    """Tests for full 4-layer pipeline."""
    
    def test_full_sanitization(self):
        """Verify all layers are applied."""
        raw = "api_key: secret123\nFile at /home/user/doc.txt"
        config = SecurityConfig()
        
        result = sanitize_context(raw, config)
        
        assert "secret123" not in result.content
        assert "user" not in result.content
        assert result.signature  # Has a signature
        assert len(result.layers_applied) > 0
    
    def test_signature_is_hash(self):
        """Verify signature is SHA256 hex."""
        result = sanitize_context("test content")
        assert len(result.signature) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in result.signature)
    
    def test_different_content_different_signature(self):
        """Verify different content produces different signatures."""
        result1 = sanitize_context("content one")
        result2 = sanitize_context("content two")
        assert result1.signature != result2.signature
