"""
AI Providers Package
=====================
Concrete LLM provider implementations.

Available Providers:
    - GroqProvider: Groq API (requires `groq` package)

Future Providers (TODO):
    - OllamaProvider: Local Ollama server
    - OpenAIProvider: OpenAI API
"""

__all__ = ["GroqProvider"]

# Lazy import to avoid requiring groq package when not using AI features
def __getattr__(name: str):
    if name == "GroqProvider":
        from devbase.ai.providers.groq import GroqProvider
        return GroqProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
