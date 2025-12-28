"""
Groq LLM Provider
==================
Implementation of LLMProvider using the Groq API.

Groq provides fast inference for open-source LLMs like Llama.
This provider uses the official `groq` Python SDK.

Requirements:
    pip install groq>=0.4.0
    
    Or with DevBase extras:
    pip install devbase[ai]

Configuration:
    API key can be provided via:
    1. GROQ_API_KEY environment variable
    2. ~/.devbase/config.toml under [ai] section

Example:
    >>> from devbase.ai.providers import GroqProvider
    >>> provider = GroqProvider()
    >>> response = provider.complete("Hello, world!")
"""
import os
from pathlib import Path
from typing import Any, Optional

from devbase.ai.exceptions import (
    InvalidAPIKeyError,
    PromptTooLongError,
    ProviderError,
    RateLimitError,
)
from devbase.ai.interface import LLMProvider

# Default configuration
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 1


def _get_api_key_from_config() -> Optional[str]:
    """Read API key from ~/.devbase/config.toml if it exists."""
    config_path = Path.home() / ".devbase" / "config.toml"
    if not config_path.exists():
        return None
    
    try:
        import toml
        config = toml.load(config_path)
        return config.get("ai", {}).get("groq_api_key")
    except Exception:
        return None


class GroqProvider(LLMProvider):
    """Groq API provider for LLM completions.
    
    Uses Groq's fast inference API with Llama models.
    
    Attributes:
        model: Model identifier (default: llama-3.3-70b-versatile).
        timeout: Request timeout in seconds (default: 30).
        max_retries: Number of retries on network errors (default: 1).
    
    Example:
        >>> provider = GroqProvider()
        >>> if provider.validate_connection():
        ...     response = provider.complete("Summarize this text...")
        ...     print(response)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize Groq provider.
        
        Args:
            api_key: Groq API key. If not provided, will attempt to read from:
                1. GROQ_API_KEY environment variable
                2. ~/.devbase/config.toml [ai].groq_api_key
            model: Model to use for completions.
            timeout: Request timeout in seconds.
            max_retries: Number of retries on transient errors.
        
        Raises:
            InvalidAPIKeyError: If no API key is found.
        """
        # Resolve API key from multiple sources
        self._api_key = (
            api_key
            or os.environ.get("GROQ_API_KEY")
            or _get_api_key_from_config()
        )
        
        if not self._api_key:
            raise InvalidAPIKeyError(
                "Groq API key not found. Set GROQ_API_KEY environment variable "
                "or run 'devbase ai config' to configure."
            )
        
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Any = None  # Lazy initialization
    
    @property
    def client(self) -> Any:
        """Lazily initialize and return the Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(
                    api_key=self._api_key,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                )
            except ImportError:
                raise ProviderError(
                    "Groq package not installed. Install with: pip install devbase[ai]"
                )
        return self._client
    
    def complete(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion using Groq API.
        
        Args:
            prompt: User message to complete.
            temperature: Creativity control (0.0-1.0).
            max_tokens: Maximum response tokens.
            system_prompt: Optional system message to set context.
            **kwargs: Additional parameters for the API.
        
        Returns:
            Generated text from the model.
        
        Raises:
            InvalidAPIKeyError: API key is invalid.
            RateLimitError: Rate limit exceeded.
            ProviderError: Other API errors.
        """
        try:
            from groq import (
                APIError,
                APIStatusError,
                AuthenticationError,
                RateLimitError as GroqRateLimitError,
            )
        except ImportError:
            raise ProviderError(
                "Groq package not installed. Install with: pip install devbase[ai]"
            )
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            
            # Extract text from response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content if content else ""
            return ""
            
        except AuthenticationError as e:
            raise InvalidAPIKeyError(
                f"Groq API key is invalid or revoked: {e}"
            )
        except GroqRateLimitError as e:
            # Try to extract retry-after header
            retry_after = None
            if hasattr(e, "response") and hasattr(e.response, "headers"):
                retry_str = e.response.headers.get("retry-after")
                if retry_str:
                    try:
                        retry_after = int(retry_str)
                    except ValueError:
                        pass
            raise RateLimitError(
                f"Groq rate limit exceeded: {e}",
                retry_after=retry_after,
            )
        except APIStatusError as e:
            # Check for context length errors
            error_msg = str(e).lower()
            if "context" in error_msg or "token" in error_msg:
                raise PromptTooLongError(
                    f"Prompt too long for model {self.model}: {e}"
                )
            raise ProviderError(f"Groq API error: {e}", original_error=e)
        except APIError as e:
            raise ProviderError(f"Groq API error: {e}", original_error=e)
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}", original_error=e)
    
    def validate_connection(self) -> bool:
        """Validate Groq API connection with a minimal request.
        
        Returns:
            True if connection is valid.
        
        Raises:
            InvalidAPIKeyError: If API key is invalid.
            ProviderError: If connection fails.
        """
        try:
            # Use a minimal completion to validate
            self.complete(
                "ping",
                temperature=0,
                max_tokens=1,
            )
            return True
        except (InvalidAPIKeyError, RateLimitError):
            raise
        except Exception as e:
            raise ProviderError(f"Connection validation failed: {e}")
