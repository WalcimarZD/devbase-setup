"""
LLM Provider Interface
=======================
Abstract base class defining the contract for LLM providers.

This follows the Ports & Adapters (Hexagonal) architecture pattern,
enabling easy substitution of providers (Groq, Ollama, OpenAI, etc.)
without changing the service layer.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    def __init__(self, message: str, original_error: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class RateLimitError(ProviderError):
    """Raised when the provider's rate limit is exceeded."""
    pass


class ConfigurationError(ProviderError):
    """Raised when there is a configuration issue (e.g., missing API key)."""
    pass


class LLMProvider(ABC):
    """Abstract interface for Large Language Model providers.
    
    Implementers must provide:
        - complete(): Generate text from a prompt
        - validate_connection(): Verify API connectivity
    """
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion from a prompt.
        
        Args:
            prompt: User input text to complete.
            system_prompt: Optional system context/instructions.
            **kwargs: Provider-specific options.
        
        Returns:
            Generated text response from the LLM.
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the provider connection is functional.
        
        Returns:
            True if connection is valid and functional.
        """
        pass
