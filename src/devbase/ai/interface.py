"""
LLM Provider Interface
=======================
Abstract base class defining the contract for LLM providers.

Follows the Ports & Adapters (Hexagonal) architecture pattern,
enabling substitution of providers (Groq, Ollama, OpenAI …)
without touching the service layer.

Exception classes live in ``devbase.ai.exceptions`` — this module
imports them for backwards-compatible re-export only.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

# Re-export so existing callers that import from this module keep working.
from devbase.ai.exceptions import (  # noqa: F401
    ConfigurationError,
    ProviderError,
    RateLimitError,
)


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
