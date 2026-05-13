"""Model implementations for API calls."""

from .base import BaseModelClient, ModelClient
from .endpoint_config import EndpointConfig, LoadBalancerConfig
from .openai_model import set_content_filter_log_path

# Lazy imports to handle missing dependencies gracefully
_openai_client_cls = None
_anthropic_client_cls = None


def OpenAIModelClient(
    load_balancer_config: LoadBalancerConfig | None = None,
    base_url: str | None = None,
    api_key_env: str | None = None,
    auth_method: str = "api_key",
    aad_scope: str = "https://cognitiveservices.azure.com/.default",
):
    """Get OpenAI model client (lazy import).

    Args:
        load_balancer_config: Optional load balancer configuration for
            multi-endpoint support.
        base_url: Optional base URL for OpenAI-compatible APIs (e.g. OpenRouter,
            Azure AI Foundry).
        api_key_env: Environment variable name for the API key when using base_url
            with ``auth_method="api_key"``.
        auth_method: ``"api_key"`` (default) or ``"azure_identity"`` (for Foundry).
        aad_scope: AAD scope for ``auth_method="azure_identity"``.
    """
    global _openai_client_cls
    if _openai_client_cls is None:
        from .openai_model import OpenAIModelClient as _OpenAI

        _openai_client_cls = _OpenAI
    return _openai_client_cls(
        load_balancer_config=load_balancer_config,
        base_url=base_url,
        api_key_env=api_key_env,
        auth_method=auth_method,
        aad_scope=aad_scope,
    )


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
    elif "/" in model_name:
        # OpenRouter model format: provider/model-name
        return OpenAIModelClient(
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
        )
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
    "set_content_filter_log_path",
]
