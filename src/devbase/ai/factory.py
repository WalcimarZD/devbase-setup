"""
AI Provider Factory
====================
Factory for instantiating LLM providers based on configuration.
"""
from pathlib import Path
from typing import Any, Dict, Optional
import toml

from devbase.ai.interface import LLMProvider, ConfigurationError
from devbase.ai.providers.mock import MockProvider
from devbase.ai.providers.groq import GroqProvider


class AIProviderFactory:
    """Factory to create and configure LLM providers."""
    
    @staticmethod
    def get_provider(root_path: Path) -> LLMProvider:
        """Get the configured LLM provider.
        
        Args:
            root_path: Project root path where config.toml is located.
            
        Returns:
            An instance of LLMProvider.
            
        Raises:
            ConfigurationError: If provider configuration is invalid or API key is missing.
        """
        config_path = root_path / "config.toml"
        config: Dict[str, Any] = {}
        
        if config_path.exists():
            try:
                config = toml.load(config_path)
            except Exception as e:
                # If we can't load config, we'll use fallbacks
                pass
        
        ai_config = config.get("ai", {})
        provider_name = ai_config.get("provider", "groq").lower()
        
        if provider_name == "mock":
            return MockProvider()
        
        # Default to groq
        try:
            # We pass the root_path to GroqProvider if it supports it, 
            # but standard GroqProvider might look for its own config.
            # Based on groq.py, it attempts to find config on its own.
            return GroqProvider()
        except Exception as e:
            # Catch InvalidAPIKeyError or others and wrap in ConfigurationError
            error_msg = str(e)
            if "API key" in error_msg or "not found" in error_msg:
                raise ConfigurationError(
                    f"Erro de Configuração: Groq API Key não encontrada em {config_path}. "
                    "Verifique a chave [ai].groq_api_key ou a variável de ambiente GROQ_API_KEY."
                ) from e
            raise ConfigurationError(f"Erro ao inicializar provedor {provider_name}: {e}") from e
