"""
Mock LLM Provider
==================
Mock implementation of LLMProvider for offline development and testing.
"""
from typing import Any, Optional
from devbase.ai.interface import LLMProvider


class MockProvider(LLMProvider):
    """Mock provider that returns predictable responses without API calls."""
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Return a mock response based on the input prompt."""
        return f"[MOCK RESPONSE] Baseado no seu prompt: {prompt[:50]}..."
    
    def validate_connection(self) -> bool:
        """Always return True for mock provider."""
        return True
