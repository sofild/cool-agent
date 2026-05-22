import asyncio
from typing import Dict, Any

from ..sandbox.executor import SandboxExecutor


class BashTools:
    """命令执行工具（支持沙箱隔离）"""

    bash_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"},
            "timeout": {"type": "integer", "description": "超时时间（秒）", "minimum": 1, "maximum": 300}
        },
        "required": ["command"]
    }

    def __init__(self, sandbox_config: Dict[str, Any] = None):
        self.sandbox_config = sandbox_config or {}
        self._executor: SandboxExecutor = None

    def _get_executor(self) -> SandboxExecutor:
        """延迟初始化执行器"""
        if self._executor is None:
            self._executor = SandboxExecutor(self.sandbox_config)
        return self._executor

    def bash(self, input_data: Dict[str, Any]) -> str:
        """执行命令（同步接口）"""
        command = input_data["command"]
        timeout = input_data.get("timeout", 30)

        executor = self._get_executor()
        try:
            return asyncio.run(executor.execute_command(command, timeout))
        except Exception as e:
            return f"Error: {str(e)}"

    async def bash_async(self, input_data: Dict[str, Any]) -> str:
        """异步执行命令"""
        command = input_data["command"]
        timeout = input_data.get("timeout", 30)

        executor = self._get_executor()
        return await executor.execute_command(command, timeout)
