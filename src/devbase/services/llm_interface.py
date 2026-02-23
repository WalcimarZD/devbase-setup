"""
LLM Provider Interface (DEPRECATED)
====================================
This module is deprecated. Use devbase.ai.interface and devbase.ai.exceptions instead.

This file re-exports symbols from the canonical AI module for backward compatibility.
It will be removed in a future release.

Migration:
    from devbase.ai.interface import LLMProvider
    from devbase.ai.exceptions import DevBaseAIError, InvalidAPIKeyError, ProviderError, RateLimitError
    from devbase.adapters.ai.groq_adapter import LLMResponse
"""
import warnings

warnings.warn(
    "devbase.services.llm_interface is deprecated. "
    "Use devbase.ai.interface and devbase.ai.exceptions instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-exports for backward compatibility
from devbase.ai.interface import LLMProvider  # noqa: F401
from devbase.ai.exceptions import (  # noqa: F401
    DevBaseAIError as LLMError,
    InvalidAPIKeyError as LLMAuthenticationError,
    ProviderError as LLMConnectionError,
    RateLimitError as LLMRateLimitError,
)
from devbase.adapters.ai.groq_adapter import LLMResponse  # noqa: F401
