"""
AI Module Exceptions
=====================
Hierarchical exception classes for AI-related errors.

Exception Hierarchy:
    DevBaseAIError (base)
    ├── ProviderError (API communication)
    │   ├── InvalidAPIKeyError (auth failures)
    │   └── RateLimitError (rate limiting)
    └── PromptTooLongError (token limit)
"""


class DevBaseAIError(Exception):
    """Base exception for all DevBase AI module errors.
    
    All AI-related exceptions inherit from this class, enabling
    catch-all handling at the CLI layer.
    """
    pass


class ProviderError(DevBaseAIError):
    """Error communicating with LLM provider API.
    
    Raised when the provider returns an error, times out,
    or encounters network issues.
    
    Attributes:
        message: Human-readable error description.
        original_error: The underlying exception from the SDK, if any.
    """
    
    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class InvalidAPIKeyError(ProviderError):
    """API key is missing, invalid, or revoked.
    
    User should verify their API key configuration.
    """
    
    def __init__(self, message: str = "API key is missing or invalid") -> None:
        super().__init__(message)


class RateLimitError(ProviderError):
    """Rate limit exceeded on LLM provider.
    
    User should wait before retrying or upgrade their plan.
    
    Attributes:
        retry_after: Seconds to wait before retrying, if provided by API.
    """
    
    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class PromptTooLongError(DevBaseAIError):
    """Prompt exceeds model's context window limit.
    
    The input data is too large for the model to process.
    User should reduce input size or use a model with larger context.
    
    Attributes:
        token_count: Estimated tokens in the prompt.
        max_tokens: Maximum allowed by the model.
    """
    
    def __init__(
        self,
        message: str = "Prompt exceeds token limit",
        token_count: int | None = None,
        max_tokens: int | None = None,
    ) -> None:
        super().__init__(message)
        self.token_count = token_count
        self.max_tokens = max_tokens
