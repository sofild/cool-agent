import json
from typing import Dict, List, Any, Callable
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    is_concurrency_safe: bool = False


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, input_schema: Dict[str, Any],
                 handler: Callable, is_concurrency_safe: bool = False):
        """
        注册工具

        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入参数Schema
            handler: 处理函数
            is_concurrency_safe: 是否支持并发执行
        """
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            is_concurrency_safe=is_concurrency_safe
        )

    def get_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义（用于LLM）

        返回 OpenAI API 格式的工具定义
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                }
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, input_data: Dict[str, Any]) -> Any:
        """
        执行工具

        Args:
            name: 工具名称
            input_data: 输入参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 如果工具不存在
        """
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        tool = self._tools[name]
        return tool.handler(input_data)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_tool(self, name: str) -> ToolDefinition:
        """获取工具定义"""
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name]
