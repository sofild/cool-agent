"""
代码执行工具

支持在沙箱中安全执行 Python、Bash、JavaScript 等代码
"""

from typing import Dict, Any

from ..sandbox.executor import SandboxExecutor


class CodeTools:
    """代码执行工具"""

    execute_code_schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的代码"},
            "language": {
                "type": "string",
                "description": "编程语言",
                "enum": ["python", "bash", "javascript"],
                "default": "python"
            },
            "timeout": {"type": "integer", "description": "超时时间（秒）", "minimum": 1, "maximum": 300, "default": 30}
        },
        "required": ["code"]
    }

    def __init__(self, sandbox_config: Dict[str, Any] = None):
        self.sandbox_config = sandbox_config or {}
        self._executor: SandboxExecutor = None

    def _get_executor(self) -> SandboxExecutor:
        """延迟初始化执行器"""
        if self._executor is None:
            self._executor = SandboxExecutor(self.sandbox_config)
        return self._executor

    def execute_code(self, input_data: Dict[str, Any]) -> str:
        """执行代码（同步接口）"""
        code = input_data["code"]
        language = input_data.get("language", "python")

        executor = self._get_executor()
        try:
            return asyncio.run(executor.execute_code(code, language))
        except Exception as e:
            return f"Error: {str(e)}"

    async def execute_code_async(self, input_data: Dict[str, Any]) -> str:
        """异步执行代码"""
        code = input_data["code"]
        language = input_data.get("language", "python")

        executor = self._get_executor()
        return await executor.execute_code(code, language)
