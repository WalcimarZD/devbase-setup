"""
AI Provider Factory
====================
Factory for instantiating LLM providers based on configuration.
"""
from pathlib import Path

from devbase.ai.exceptions import ConfigurationError
from devbase.ai.interface import LLMProvider
from devbase.ai.providers.mock import MockProvider
from devbase.ai.providers.groq import GroqProvider
from devbase.utils.config import Config


class AIProviderFactory:
    """Factory that creates LLM providers from workspace configuration."""

    @staticmethod
    def get_provider(root_path: Path) -> LLMProvider:
        """Return the configured LLM provider for the given workspace root.

        Reads ``[ai].provider`` from ``config.toml`` (defaults to ``groq``).
        Passes *root_path* to the provider so it can resolve the API key.

        Args:
            root_path: Workspace root directory.

        Returns:
            A ready-to-use ``LLMProvider`` instance.

        Raises:
            ConfigurationError: If the provider cannot be initialised.
        """
        config = Config(root=root_path)
        provider_name = config.get("ai.provider", "groq").lower()

        if provider_name == "mock":
            return MockProvider()

        try:
            return GroqProvider(root=root_path)
        except Exception as exc:
            error_msg = str(exc)
            if "API key" in error_msg or "not found" in error_msg:
                raise ConfigurationError(
                    f"Groq API key not found. "
                    "Set GROQ_API_KEY or run 'devbase ai config'."
                ) from exc
            raise ConfigurationError(
                f"Failed to initialise provider '{provider_name}': {exc}"
            ) from exc
