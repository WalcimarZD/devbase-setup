"""
LLM Provider Interface
=======================
Abstract base class defining the contract for LLM providers.

This follows the Ports & Adapters (Hexagonal) architecture pattern,
enabling easy substitution of providers (Groq, Ollama, OpenAI, etc.)
without changing the service layer.

Example:
    >>> class MyProvider(LLMProvider):
    ...     def complete(self, prompt, **kwargs):
    ...         return "Generated text"
    ...     def validate_connection(self):
    ...         return True
"""
from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract interface for Large Language Model providers.
    
    Implementers must provide:
        - complete(): Generate text from a prompt
        - validate_connection(): Verify API connectivity
    
    All providers should handle their own authentication and
    convert SDK-specific exceptions to DevBase AI exceptions.
    """
    
    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> str:
        """Generate text completion from a prompt.
        
        Args:
            prompt: Input text to complete.
            temperature: Creativity control (0.0 = deterministic, 1.0 = creative).
                Lower values produce more focused, consistent output.
                Default is 0.3 for reliable structured responses.
            max_tokens: Maximum tokens in the response.
            **kwargs: Provider-specific options (e.g., stop sequences).
        
        Returns:
            Generated text response from the LLM.
        
        Raises:
            InvalidAPIKeyError: API key is missing or invalid.
            RateLimitError: Rate limit exceeded on provider.
            ProviderError: Other API or network errors.
            PromptTooLongError: Prompt exceeds model's context limit.
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the provider connection is functional.
        
        Performs a lightweight API call to verify:
            - API key is valid
            - Network connectivity is working
            - Provider service is available
        
        Returns:
            True if connection is valid and functional.
        
        Raises:
            InvalidAPIKeyError: API key is invalid.
            ProviderError: Network or service error.
        """
        pass
