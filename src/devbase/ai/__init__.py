"""
DevBase AI Module
==================
AI-powered commands using Groq LLM backend.

Exports:
    - LLMProvider: Abstract base class for LLM providers
    - AIService: High-level AI service orchestrator
    - GroqProvider: Groq implementation (requires `groq` package)
"""
from devbase.ai.exceptions import (
    DevBaseAIError,
    InvalidAPIKeyError,
    PromptTooLongError,
    ProviderError,
    RateLimitError,
)
from devbase.ai.interface import LLMProvider
from devbase.ai.models import Insight, OrganizationSuggestion
from devbase.ai.service import AIService

__all__ = [
    # Exceptions
    "DevBaseAIError",
    "ProviderError",
    "InvalidAPIKeyError",
    "RateLimitError",
    "PromptTooLongError",
    # Interface
    "LLMProvider",
    # Service
    "AIService",
    # Models
    "OrganizationSuggestion",
    "Insight",
]
