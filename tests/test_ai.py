"""
Tests for AI Module
====================
Unit tests for LLM interface, Groq adapter, and AI CLI commands.
Uses mocking to avoid real API calls.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from devbase.main import app
from devbase.ai.exceptions import (
    DevBaseAIError,
    InvalidAPIKeyError,
    ProviderError,
)
from devbase.ai.models import LLMResponse


runner = CliRunner()


# =============================================================================
# LLM Interface Tests
# =============================================================================

class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_llm_response_is_immutable(self):
        """Verify LLMResponse is frozen (immutable)."""
        response = LLMResponse(
            content="Hello",
            model="test-model",
            tokens_used=10,
            latency_ms=50.0,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            response.content = "Modified"
    
    def test_llm_response_attributes(self):
        """Verify LLMResponse stores all attributes correctly."""
        response = LLMResponse(
            content="Test content",
            model="llama-3.1-8b-instant",
            tokens_used=42,
            latency_ms=123.45,
        )
        
        assert response.content == "Test content"
        assert response.model == "llama-3.1-8b-instant"
        assert response.tokens_used == 42
        assert response.latency_ms == 123.45


# =============================================================================
# Groq Adapter Tests (Mocked)
# =============================================================================

class TestGroqProvider:
    """Tests for GroqProvider with mocked API calls."""

    def test_groq_provider_requires_api_key(self):
        """Verify GroqProvider raises InvalidAPIKeyError when no key is available."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("devbase.ai.providers.groq.ConfigResolver.resolve_api_key", return_value=None):
                with pytest.raises(InvalidAPIKeyError):
                    from devbase.ai.providers.groq import GroqProvider
                    GroqProvider(api_key=None)

    def test_groq_provider_accepts_explicit_key(self):
        """Verify GroqProvider accepts an explicit API key."""
        from devbase.ai.providers.groq import GroqProvider

        provider = GroqProvider(api_key="test-key-12345")
        assert provider.api_key == "test-key-12345"

    @patch("devbase.ai.providers.groq.groq")
    def test_complete_calls_api(self, mock_groq_mod):
        """Verify complete() calls the Groq API and returns a string."""
        from devbase.ai.providers.groq import GroqProvider

        mock_client = MagicMock()
        mock_groq_mod.Groq.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mocked response"))]
        mock_client.chat.completions.create.return_value = mock_response

        provider = GroqProvider(api_key="test-key")
        result = provider.complete("Hello, world!")

        assert result == "Mocked response"
        mock_client.chat.completions.create.assert_called_once()

    @patch("devbase.ai.providers.groq.groq")
    def test_complete_raises_rate_limit(self, mock_groq_mod):
        """Verify RateLimitError is raised when Groq throttles the request."""
        import groq as groq_lib
        from devbase.ai.exceptions import RateLimitError
        from devbase.ai.providers.groq import GroqProvider

        mock_client = MagicMock()
        mock_groq_mod.Groq.return_value = mock_client
        mock_groq_mod.RateLimitError = groq_lib.RateLimitError
        mock_client.chat.completions.create.side_effect = groq_lib.RateLimitError(
            message="rate limited", response=MagicMock(), body={}
        )

        provider = GroqProvider(api_key="test-key")
        with pytest.raises(RateLimitError):
            provider.complete("ping")

    @patch("devbase.ai.providers.groq.groq")
    def test_complete_raises_invalid_api_key(self, mock_groq_mod):
        """Verify InvalidAPIKeyError is raised on authentication failure."""
        import groq as groq_lib
        from devbase.ai.providers.groq import GroqProvider

        mock_client = MagicMock()
        mock_groq_mod.Groq.return_value = mock_client
        mock_groq_mod.AuthenticationError = groq_lib.AuthenticationError
        mock_client.chat.completions.create.side_effect = groq_lib.AuthenticationError(
            message="invalid key", response=MagicMock(), body={}
        )

        provider = GroqProvider(api_key="bad-key")
        with pytest.raises(InvalidAPIKeyError):
            provider.complete("ping")


# =============================================================================
# AI CLI Command Tests
# =============================================================================

class TestAICommands:
    """Tests for AI CLI commands."""
    
    def test_ai_help_shows_subcommands(self):
        """Verify 'devbase ai --help' shows available subcommands."""
        result = runner.invoke(app, ["ai", "--help"])
        
        assert result.exit_code == 0
        assert "chat" in result.stdout
        assert "classify" in result.stdout
        assert "summarize" in result.stdout
        assert "status" in result.stdout
    
    def test_ai_status_runs_without_api_key(self):
        """Verify 'devbase ai status' works without API key."""
        result = runner.invoke(app, ["ai", "status"])
        
        # Should not crash, even without API key
        assert result.exit_code == 0
        assert "AI Status" in result.stdout or "GROQ_API_KEY" in result.stdout
    
    @patch("devbase.commands.ai._get_provider")
    def test_ai_chat_displays_response(self, mock_get_provider):
        """Verify 'devbase ai chat' displays LLM response."""
        mock_provider = MagicMock()
        # commands/ai.py chat() calls provider.complete(), not generate()
        mock_provider.complete.return_value = "Mocked AI response"
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["ai", "chat", "Hello"])
        
        assert result.exit_code == 0
        assert "Mocked AI response" in result.stdout
    
    @patch("devbase.commands.ai._get_provider")
    def test_ai_classify_displays_category(self, mock_get_provider):
        """Verify 'devbase ai classify' displays category result."""
        mock_provider = MagicMock()
        # commands/ai.py classify() calls provider.complete() with raw prompt
        mock_provider.complete.return_value = "bug"
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["ai", "classify", "Fix button", "-c", "bug,feature"])
        
        assert result.exit_code == 0
        assert "bug" in result.stdout


# =============================================================================
# Integration Test (Worker)
# =============================================================================

class TestAsyncWorker:
    """Tests for AsyncWorker AI task processing."""
    
    def test_worker_can_be_instantiated(self, tmp_path):
        """Verify AIWorker can be created with a db path."""
        from devbase.services.async_worker import AIWorker
        
        db_path = tmp_path / "test.duckdb"
        worker = AIWorker(db_path)
        
        assert worker.db_path == db_path
        assert not worker.is_running()
    
    def test_worker_register_handler(self, tmp_path):
        """Verify custom handlers can be registered."""
        from devbase.services.async_worker import AIWorker
        
        worker = AIWorker(tmp_path / "test.duckdb")
        
        def custom_handler(payload: str) -> str:
            return "custom result"
        
        worker.register_handler("custom_task", custom_handler)
        
        assert "custom_task" in worker.handlers
        assert worker.handlers["custom_task"]("test") == "custom result"
