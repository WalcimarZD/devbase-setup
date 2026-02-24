"""
Groq LLM Adapter (Legacy Compatibility)
========================================
Concrete implementation of LLMProvider for Groq API.

This adapter implements the services/llm_interface.LLMProvider contract
and is used by RoutineAgent and other services that depend on
the `generate()`, `classify()`, and `summarize()` convenience methods.

For the Ports & Adapters (ai.interface.LLMProvider) implementation,
see: devbase.ai.providers.groq

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import TYPE_CHECKING

from devbase.ai.exceptions import (
    DevBaseAIError,
    InvalidAPIKeyError,
    ProviderError,
    RateLimitError,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Default model for Groq (fast and capable)
DEFAULT_MODEL = "llama-3.1-8b-instant"


# Immutable response dataclass
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    """Immutable response from LLM.

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


class GroqProvider:
    """
    Groq API provider implementation.

    Uses the official Groq Python SDK for API calls.
    Implements retry logic with exponential backoff.

    Environment Variables:
        GROQ_API_KEY: Required API key for authentication

    Example:
        provider = GroqProvider()  # Uses env var
        response = provider.generate("Hello!")
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = DEFAULT_MODEL,
        max_retries: int = 3,
    ):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key (falls back to GROQ_API_KEY env var)
            default_model: Default model for generation
            max_retries: Maximum retry attempts on transient errors

        Raises:
            InvalidAPIKeyError: If no API key is provided or found
        """
        # Try config file if env var missing
        if not api_key and not os.environ.get("GROQ_API_KEY"):
            try:
                import toml
                from devbase.utils.paths import get_config_path
                config_path = get_config_path()
                if config_path.exists():
                    config = toml.load(config_path)
                    api_key = config.get("ai", {}).get("groq_api_key")
            except (ImportError, OSError, ValueError) as e:
                logger.debug(f"Could not read config file for API key: {e}")

        self.api_key = api_key or os.environ.get("GROQ_API_KEY")

        if not self.api_key:
            raise InvalidAPIKeyError(
                "GROQ_API_KEY not found. Set it via environment variable or pass api_key."
            )

        self.default_model = default_model
        self.max_retries = max_retries
        self._client = None  # Lazy initialization

    @property
    def client(self):
        """Lazy-load Groq client to preserve cold start performance."""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError as e:
                raise ProviderError(
                    "Groq SDK not installed. Run: uv add groq"
                ) from e
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate text completion using Groq API."""
        model = model or self.default_model
        start_time = time.perf_counter()

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                latency_ms = (time.perf_counter() - start_time) * 1000

                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    model=model,
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    latency_ms=latency_ms,
                )

            except Exception as e:
                if self._is_rate_limit_error(e):
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise RateLimitError(
                        f"Rate limit exceeded after {self.max_retries} retries"
                    ) from e

                if self._is_auth_error(e):
                    raise InvalidAPIKeyError("Invalid Groq API key") from e

                if self._is_connection_error(e):
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    raise ProviderError(f"Connection failed: {e}") from e

                raise ProviderError(f"Groq API error: {e}") from e

        raise ProviderError("Max retries exceeded")

    def classify(
        self,
        text: str,
        categories: list[str],
        *,
        model: str | None = None,
    ) -> str:
        """Classify text into one of the given categories."""
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following text into exactly ONE of these categories: {categories_str}

Text: {text}

Respond with ONLY the category name, nothing else."""

        response = self.generate(prompt, model=model, max_tokens=50, temperature=0.0)

        result = response.content.strip().lower()

        for category in categories:
            if category.lower() in result:
                return category

        return categories[0] if categories else "unknown"

    def summarize(
        self,
        text: str,
        *,
        max_length: int = 100,
        model: str | None = None,
    ) -> str:
        """Summarize text to specified length."""
        prompt = f"""Summarize the following text in {max_length} words or less.
Be concise and capture the key points.

Text: {text}

Summary:"""

        response = self.generate(prompt, model=model, max_tokens=max_length * 2, temperature=0.3)
        return response.content.strip()

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return "rate" in error_str and "limit" in error_str

    def _is_auth_error(self, error: Exception) -> bool:
        """Check if error is an authentication error."""
        error_str = str(error).lower()
        return "auth" in error_str or "unauthorized" in error_str or "api key" in error_str

    def _is_connection_error(self, error: Exception) -> bool:
        """Check if error is a connection error."""
        error_str = str(error).lower()
        return "connection" in error_str or "timeout" in error_str or "network" in error_str
