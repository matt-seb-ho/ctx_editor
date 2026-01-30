"""Model implementations for API calls."""

from .base import BaseModelClient, ModelClient

# Lazy imports to handle missing dependencies gracefully
_openai_client = None
_anthropic_client = None


def OpenAIModelClient():
    """Get OpenAI model client (lazy import)."""
    global _openai_client
    if _openai_client is None:
        from .openai_model import OpenAIModelClient as _OpenAI

        _openai_client = _OpenAI
    return _openai_client()


def AnthropicModelClient():
    """Get Anthropic model client (lazy import)."""
    global _anthropic_client
    if _anthropic_client is None:
        from .anthropic_model import AnthropicModelClient as _Anthropic

        _anthropic_client = _Anthropic
    return _anthropic_client()


def get_model_client(model_name: str = "gpt-4o-mini"):
    """Factory function to get the appropriate model client.

    Args:
        model_name: Name of the model to use.

    Returns:
        Configured model client instance.
    """
    if "claude" in model_name.lower() or "anthropic" in model_name.lower():
        return AnthropicModelClient()
    else:
        return OpenAIModelClient()


__all__ = [
    "ModelClient",
    "BaseModelClient",
    "OpenAIModelClient",
    "AnthropicModelClient",
    "get_model_client",
]
