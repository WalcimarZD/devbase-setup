"""
LLM Provider Interface
======================
Abstract interface for LLM providers (Groq, OpenAI, etc).

Follows ISP (Interface Segregation Principle) - small, focused interface.
Allows future providers without modifying existing code (OCP).

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class LLMResponse:
    """
    Immutable response from LLM.
    
    Attributes:
        content: Generated text content
        model: Model used for generation
        tokens_used: Total tokens consumed
        latency_ms: Response latency in milliseconds
    """
    content: str
    model: str
    tokens_used: int
    latency_ms: float


class LLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    
    All providers must implement these methods.
    Use dependency injection to swap providers at runtime.
    
    Example:
        provider = GroqProvider(api_key="...")
        response = provider.generate("Hello, world!")
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            model: Model identifier (provider-specific default if None)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMError: On API or network errors
        """
        ...
    
    @abstractmethod
    def classify(
        self,
        text: str,
        categories: list[str],
        *,
        model: str | None = None,
    ) -> str:
        """
        Classify text into one of the given categories.
        
        Args:
            text: Text to classify
            categories: List of valid category names
            model: Model identifier (provider-specific default if None)
            
        Returns:
            Category name from the provided list
            
        Raises:
            LLMError: On API or classification errors
        """
        ...
    
    @abstractmethod
    def summarize(
        self,
        text: str,
        *,
        max_length: int = 100,
        model: str | None = None,
    ) -> str:
        """
        Summarize text to specified length.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length in words
            model: Model identifier (provider-specific default if None)
            
        Returns:
            Summarized text
            
        Raises:
            LLMError: On API errors
        """
        ...


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class LLMConnectionError(LLMError):
    """Network or connection error."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMAuthenticationError(LLMError):
    """Invalid API key or authentication failure."""
    pass
