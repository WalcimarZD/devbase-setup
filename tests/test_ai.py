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
from devbase.services.llm_interface import (
    LLMProvider,
    LLMResponse,
    LLMError,
    LLMAuthenticationError,
)


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
        """Verify GroqProvider raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMAuthenticationError):
                from devbase.adapters.ai.groq_adapter import GroqProvider
                # Force reimport to clear cached key
                GroqProvider(api_key=None)
    
    def test_groq_provider_accepts_explicit_key(self):
        """Verify GroqProvider accepts explicit API key."""
        from devbase.adapters.ai.groq_adapter import GroqProvider
        
        provider = GroqProvider(api_key="test-key-12345")
        assert provider.api_key == "test-key-12345"
    
    @patch("devbase.adapters.ai.groq_adapter.GroqProvider.client", new_callable=MagicMock)
    def test_generate_calls_api(self, mock_client):
        """Verify generate() calls the Groq API correctly."""
        from devbase.adapters.ai.groq_adapter import GroqProvider
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mocked response"))]
        mock_response.usage = MagicMock(total_tokens=25)
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        response = provider.generate("Hello, world!")
        
        assert response.content == "Mocked response"
        assert response.tokens_used == 25
        mock_client.chat.completions.create.assert_called_once()
    
    @patch("devbase.adapters.ai.groq_adapter.GroqProvider.client", new_callable=MagicMock)
    def test_classify_returns_valid_category(self, mock_client):
        """Verify classify() returns a category from the provided list."""
        from devbase.adapters.ai.groq_adapter import GroqProvider
        
        # Mock returns "bug" in response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="bug"))]
        mock_response.usage = MagicMock(total_tokens=15)
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        result = provider.classify("Fix login button", ["feature", "bug", "docs"])
        
        assert result == "bug"
    
    @patch("devbase.adapters.ai.groq_adapter.GroqProvider.client", new_callable=MagicMock)
    def test_summarize_returns_text(self, mock_client):
        """Verify summarize() returns summarized text."""
        from devbase.adapters.ai.groq_adapter import GroqProvider
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="This is a summary."))]
        mock_response.usage = MagicMock(total_tokens=20)
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        result = provider.summarize("Long text here..." * 100, max_length=50)
        
        assert result == "This is a summary."


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
        assert "Worker" in result.stdout or "Metric" in result.stdout
    
    @patch("devbase.commands.ai._get_provider")
    def test_ai_chat_displays_response(self, mock_get_provider):
        """Verify 'devbase ai chat' displays LLM response."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = LLMResponse(
            content="Mocked AI response",
            model="test-model",
            tokens_used=10,
            latency_ms=50.0,
        )
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["ai", "chat", "Hello"])
        
        assert result.exit_code == 0
        assert "Mocked AI response" in result.stdout
    
    @patch("devbase.commands.ai._get_provider")
    def test_ai_classify_displays_category(self, mock_get_provider):
        """Verify 'devbase ai classify' displays category result."""
        mock_provider = MagicMock()
        mock_provider.classify.return_value = "bug"
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
