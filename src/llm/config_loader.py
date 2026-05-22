"""
LLM 配置加载器
支持统一配置格式和备用模型
"""
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """单个LLM配置"""
    model: str
    base_url: str
    api_key: str
    api_type: str  # openai / anthropic
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120


@dataclass
class LLMConfigSet:
    """LLM配置集合"""
    primary: LLMConfig
    backups: List[LLMConfig] = field(default_factory=list)


def _is_local_url(url: str) -> bool:
    """判断是否为本地模型地址"""
    if not url:
        return False
    local_indicators = [
        "localhost",
        "127.0.0.1",
        "192.168.",
        "10.0.",
        ":11434",  # ollama默认端口
    ]
    return any(indicator in url for indicator in local_indicators)


def _resolve_provider(api_type: str, base_url: str) -> str:
    """
    解析实际的 provider

    逻辑:
    - 如果 base_url 是本地地址，使用 local 客户端
    - 否则使用 api_type 对应的客户端
    """
    if _is_local_url(base_url):
        return "local"
    return api_type


def load_llm_config_from_env() -> LLMConfigSet:
    """
    从环境变量加载LLM配置

    支持格式:
    - 主模型: LLM_MODEL, LLM_BASE_URL, LLM_API_KEY, LLM_API_TYPE
    - 备用模型: BACKUP{n}_LLM_MODEL, BACKUP{n}_LLM_BASE_URL, ...
    """
    # 加载主模型配置
    base_url = os.getenv("LLM_BASE_URL", "")
    api_type = os.getenv("LLM_API_TYPE", "openai").lower()

    primary = LLMConfig(
        model=os.getenv("LLM_MODEL", "gpt-4o"),
        base_url=base_url,
        api_key=os.getenv("LLM_API_KEY", ""),
        api_type=api_type,
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        timeout=int(os.getenv("LLM_TIMEOUT", "120")),
    )

    # 加载备用模型配置
    backups = []
    for i in range(1, 10):  # 支持最多9个备用模型
        prefix = f"BACKUP{i}_"
        backup_model = os.getenv(f"{prefix}LLM_MODEL")

        if backup_model:
            backup_base_url = os.getenv(f"{prefix}LLM_BASE_URL", "")
            backup_api_type = os.getenv(f"{prefix}LLM_API_TYPE", "openai").lower()

            backups.append(LLMConfig(
                model=backup_model,
                base_url=backup_base_url,
                api_key=os.getenv(f"{prefix}LLM_API_KEY", ""),
                api_type=backup_api_type,
                max_tokens=int(os.getenv(f"{prefix}LLM_MAX_TOKENS", "4096")),
                temperature=float(os.getenv(f"{prefix}LLM_TEMPERATURE", "0.7")),
                timeout=int(os.getenv(f"{prefix}LLM_TIMEOUT", "120")),
            ))

    return LLMConfigSet(primary=primary, backups=backups)


def llm_config_to_dict(config: LLMConfig) -> Dict[str, Any]:
    """将LLMConfig转换为字典（供factory使用）"""
    provider = _resolve_provider(config.api_type, config.base_url)

    return {
        "model": config.model,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "provider": provider,
        "api_type": config.api_type,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
        "timeout": config.timeout,
    }
