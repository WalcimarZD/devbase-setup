"""
Groq LLM Provider
==================
Implementation of LLMProvider using the Groq API.

Requirements:
    pip install devbase[ai]

Configuration:
    API key resolved via ConfigResolver (ENV > config.toml > None).
"""
from pathlib import Path
from typing import Any, Optional

try:
    import groq  # type: ignore
except ImportError:
    groq = None  # type: ignore

from devbase.ai.exceptions import (
    InvalidAPIKeyError,
    PromptTooLongError,
    ProviderError,
    RateLimitError,
)
from devbase.ai.interface import LLMProvider
from devbase.utils.config import ConfigResolver

# Default configuration constants
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 1


class GroqProvider(LLMProvider):
    """Groq API provider for LLM completions.

    Uses Groq's fast inference API with Llama models.
    API key is resolved in order: explicit arg > GROQ_API_KEY env > config.toml.

    Args:
        api_key: Explicit API key (overrides all other sources).
        model: Model identifier.
        timeout: Request timeout in seconds.
        max_retries: Retries on transient network errors.
        root: Workspace root for local config resolution.

    Raises:
        InvalidAPIKeyError: If no API key is found from any source.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        root: Optional[Path] = None,
    ) -> None:
        self.root = root
        self._api_key = ConfigResolver.resolve_api_key("groq", explicit=api_key, root=root)

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
    def api_key(self) -> str:
        """Expose configured API key for backwards compatibility in tests."""
        return self._api_key

    @property
    def client(self) -> Any:
        """Lazily initialise the Groq SDK client."""
        if self._client is None:
            if groq is None:
                raise ProviderError(
                    "Groq package not installed. Install with: pip install devbase[ai]"
                )
            self._client = groq.Groq(
                api_key=self._api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
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
        """Generate a text completion using the Groq API.

        Args:
            prompt: User message.
            temperature: Creativity control (0.0–1.0).
            max_tokens: Maximum response tokens.
            system_prompt: Optional system context.
            **kwargs: Additional Groq API parameters.

        Returns:
            Generated text string.

        Raises:
            InvalidAPIKeyError: API key is invalid.
            RateLimitError: Rate limit exceeded.
            PromptTooLongError: Prompt exceeds context window.
            ProviderError: Any other API error.
        """
        if groq is None:
            raise ProviderError(
                "Groq package not installed. Install with: pip install devbase[ai]"
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        auth_error_type = getattr(groq, "AuthenticationError", None)
        rate_limit_error_type = getattr(groq, "RateLimitError", None)
        api_status_error_type = getattr(groq, "APIStatusError", None)
        api_error_type = getattr(groq, "APIError", None)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content if content else ""
            return ""
        except Exception as exc:
            is_auth_error = (
                isinstance(auth_error_type, type)
                and issubclass(auth_error_type, BaseException)
                and isinstance(exc, auth_error_type)
            )
            if is_auth_error:
                raise InvalidAPIKeyError(f"Groq API key is invalid or revoked: {exc}")

            is_rate_limit_error = (
                isinstance(rate_limit_error_type, type)
                and issubclass(rate_limit_error_type, BaseException)
                and isinstance(exc, rate_limit_error_type)
            )
            if is_rate_limit_error:
                retry_after: Optional[int] = None
                if hasattr(exc, "response") and hasattr(exc.response, "headers"):
                    retry_str = exc.response.headers.get("retry-after")
                    if retry_str:
                        try:
                            retry_after = int(retry_str)
                        except ValueError:
                            pass
                raise RateLimitError(
                    f"Groq rate limit exceeded: {exc}",
                    retry_after=retry_after,
                )

            is_api_status_error = (
                isinstance(api_status_error_type, type)
                and issubclass(api_status_error_type, BaseException)
                and isinstance(exc, api_status_error_type)
            )
            if is_api_status_error:
                error_msg = str(exc).lower()
                if "context" in error_msg or "token" in error_msg:
                    raise PromptTooLongError(f"Prompt too long for model {self.model}: {exc}")
                raise ProviderError(f"Groq API error: {exc}", original_error=exc)

            is_api_error = (
                isinstance(api_error_type, type)
                and issubclass(api_error_type, BaseException)
                and isinstance(exc, api_error_type)
            )
            if is_api_error:
                raise ProviderError(f"Groq API error: {exc}", original_error=exc)

            raise ProviderError(f"Unexpected error: {exc}", original_error=exc)

    def validate_connection(self) -> bool:
        """Validate Groq API connectivity with a minimal request.

        Returns:
            ``True`` if the connection is healthy.

        Raises:
            InvalidAPIKeyError: If the API key is invalid.
            ProviderError: If the connection fails for any other reason.
        """
        try:
            self.complete("ping", temperature=0, max_tokens=1)
            return True
        except (InvalidAPIKeyError, RateLimitError):
            raise
        except Exception as exc:
            raise ProviderError(f"Connection validation failed: {exc}")
