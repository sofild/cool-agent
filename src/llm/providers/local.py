from typing import Dict, Any, Optional, List

import httpx

from ..client import LLMClient, Message, ToolCall, LLMResponse


class LocalClient(LLMClient):
    """本地模型客户端（兼容OpenAI API）"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
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

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            message = data["choices"][0]["message"]
            return LLMResponse(
                content=message.get("content", ""),
                tool_calls=[],
                usage=data.get("usage", {}),
                model=self.model
            )
        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e, 'response') else 'unknown'
            raise Exception(f"HTTP {e.response.status_code}: {error_body}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response format: {str(e)}")
        except Exception as e:
            raise Exception(f"LocalClient error: {str(e)}")

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.config.get("base_url"))
