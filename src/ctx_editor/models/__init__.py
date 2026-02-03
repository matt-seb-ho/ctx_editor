"""Model implementations for API calls."""

from .base import BaseModelClient, ModelClient
from .endpoint_config import EndpointConfig, LoadBalancerConfig

# Lazy imports to handle missing dependencies gracefully
_openai_client_cls = None
_anthropic_client_cls = None


def OpenAIModelClient(load_balancer_config: LoadBalancerConfig | None = None):
    """Get OpenAI model client (lazy import).

    Args:
        load_balancer_config: Optional load balancer configuration for
            multi-endpoint support.
    """
    global _openai_client_cls
    if _openai_client_cls is None:
        from .openai_model import OpenAIModelClient as _OpenAI

        _openai_client_cls = _OpenAI
    return _openai_client_cls(load_balancer_config=load_balancer_config)


def AnthropicModelClient():
    """Get Anthropic model client (lazy import)."""
    global _anthropic_client_cls
    if _anthropic_client_cls is None:
        from .anthropic_model import AnthropicModelClient as _Anthropic

        _anthropic_client_cls = _Anthropic
    return _anthropic_client_cls()


def get_model_client(
    model_name: str = "gpt-4o-mini",
    load_balancer_config: LoadBalancerConfig | None = None,
):
    """Factory function to get the appropriate model client.

    Args:
        model_name: Name of the model to use.
        load_balancer_config: Optional load balancer config for OpenAI clients.

    Returns:
        Configured model client instance.
    """
    if "claude" in model_name.lower() or "anthropic" in model_name.lower():
        return AnthropicModelClient()
    else:
        return OpenAIModelClient(load_balancer_config=load_balancer_config)


__all__ = [
    "ModelClient",
    "BaseModelClient",
    "OpenAIModelClient",
    "AnthropicModelClient",
    "get_model_client",
    "EndpointConfig",
    "LoadBalancerConfig",
]
