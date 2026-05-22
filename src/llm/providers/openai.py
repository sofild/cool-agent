import json as json_mod
from typing import Dict, Any, Optional, List

import httpx

from ..client import LLMClient, Message, ToolCall, LLMResponse


class OpenAICompatibleClient(LLMClient):
    """OpenAI API 兼容客户端

    支持所有兼容 OpenAI API 格式的服务:
    - OpenAI 官方
    - Azure OpenAI
    - 阿里云百炼
    - DeepSeek
    - 其他兼容服务
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.api_key = config.get("api_key", "")
        timeout = config.get("timeout", 120)
        self.client = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            message = data["choices"][0]["message"]
            content = message.get("content", "")

            tool_calls = []
            if message.get("tool_calls"):
                for tc in message["tool_calls"]:
                    tool_calls.append(ToolCall(
                        id=tc.get("id", ""),
                        name=tc["function"]["name"],
                        arguments=json_mod.loads(tc["function"]["arguments"])
                    ))

            usage = data.get("usage", {})
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                usage={
                    "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                    "completion_tokens": int(usage.get("completion_tokens", 0))
                },
                model=data.get("model", self.model)
            )
        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e, 'response') else 'unknown'
            raise Exception(f"HTTP {e.response.status_code}: {error_body}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response format: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAICompatibleClient error: {str(e)}")

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.config.get("api_key"))
