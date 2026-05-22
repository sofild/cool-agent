from typing import Dict, Any

from .client import LLMClient
from .providers.anthropic import AnthropicClient
from .providers.openai import OpenAICompatibleClient
from .providers.local import LocalClient


def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    根据配置创建对应的LLM客户端

    Args:
        config: 配置字典，必须包含 provider/api_type 字段

    Returns:
        LLMClient实例

    Raises:
        ValueError: 如果供应商未知
    """
    # 支持 provider 或 api_type 字段
    provider = config.get("provider", config.get("api_type", "openai")).lower()

    providers = {
        "anthropic": AnthropicClient,
        "openai": OpenAICompatibleClient,
        "azure": OpenAICompatibleClient,
        "aliyun": OpenAICompatibleClient,
        "deepseek": OpenAICompatibleClient,
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
