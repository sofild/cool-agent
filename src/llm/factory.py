from typing import Dict, Any

from .client import LLMClient
from .providers.anthropic import AnthropicClient
from .providers.openai import OpenAIClient
from .providers.local import LocalClient


def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    根据配置创建对应的LLM客户端

    Args:
        config: 配置字典，必须包含 provider 字段

    Returns:
        LLMClient实例

    Raises:
        ValueError: 如果供应商未知
    """
    provider = config.get("provider", "anthropic").lower()

    providers = {
        "anthropic": AnthropicClient,
        "openai": OpenAIClient,
        "azure": OpenAIClient,
        "local": LocalClient,
    }

    if provider not in providers:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(providers.keys())}"
        )

    client = providers[provider](config)

    if not client.validate_config():
        raise ValueError(f"Invalid configuration for provider: {provider}")

    return client
