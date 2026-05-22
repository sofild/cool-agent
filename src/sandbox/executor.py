"""
沙箱执行器

提供命令执行和代码执行的统一接口，优先使用 OpenSandbox，不可用时降级到本地执行
"""

import subprocess
import time
from typing import Dict, Any, Optional

from .manager import SandboxManager
from .config import SandboxConfig


class SandboxExecutor:
    """沙箱执行器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = SandboxConfig.from_dict(config or {})
        self.manager = SandboxManager(self.config)
        self._initialized = False

    async def initialize(self):
        """初始化执行器"""
        if not self._initialized:
            await self.manager.initialize()
            self._initialized = True

    async def execute_command(self, command: str, timeout: int = 30) -> str:
        """执行命令"""
        await self.initialize()

        if self.manager.is_available:
            return await self._execute_in_sandbox(command, timeout)
        else:
            return await self._execute_local(command, timeout)

    async def _execute_in_sandbox(self, command: str, timeout: int) -> str:
        """在沙箱中执行命令"""
        sandbox = await self.manager.acquire_sandbox()
        if not sandbox:
            return await self._execute_local(command, timeout)

        try:
            execution = await sandbox.commands.run(command, timeout=timeout)
            return self._format_execution_result(execution)
        except Exception as e:
            return f"Error (sandbox): {e}"
        finally:
            await self.manager.release_sandbox(sandbox)

    async def _execute_local(self, command: str, timeout: int) -> str:
        """在本地执行命令（降级方案）"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}"

    def _format_execution_result(self, execution) -> str:
        """格式化沙箱执行结果"""
        lines = []
        if hasattr(execution, "logs") and execution.logs:
            if hasattr(execution.logs, "stdout") and execution.logs.stdout:
                for line in execution.logs.stdout:
                    lines.append(line.text if hasattr(line, "text") else str(line))
            if hasattr(execution.logs, "stderr") and execution.logs.stderr:
                for line in execution.logs.stderr:
                    lines.append(f"[stderr] {line.text if hasattr(line, 'text') else str(line)}")
        if hasattr(execution, "exit_code") and execution.exit_code != 0:
            lines.append(f"[exit code: {execution.exit_code}]")
        return "\n".join(lines) if lines else "(no output)"

    async def execute_code(self, code: str, language: str = "python") -> str:
        """执行代码"""
        await self.initialize()

        if self.manager.is_available:
            return await self._execute_code_in_sandbox(code, language)
        else:
            return await self._execute_code_local(code, language)

    async def _execute_code_in_sandbox(self, code: str, language: str) -> str:
        """在沙箱中执行代码"""
        sandbox = await self.manager.acquire_sandbox()
        if not sandbox:
            return await self._execute_code_local(code, language)

        try:
            from code_interpreter import CodeInterpreter, SupportedLanguage

            interpreter = await CodeInterpreter.create(sandbox)

            lang_map = {
                "python": SupportedLanguage.PYTHON,
                "bash": SupportedLanguage.BASH,
                "javascript": SupportedLanguage.JAVASCRIPT,
            }
            lang = lang_map.get(language.lower(), SupportedLanguage.PYTHON)

            result = await interpreter.codes.run(code, language=lang)
            return self._format_code_result(result)
        except Exception as e:
            return f"Error (sandbox code): {e}"
        finally:
            await self.manager.release_sandbox(sandbox)

    async def _execute_code_local(self, code: str, language: str) -> str:
        """在本地执行代码（降级方案）"""
        if language.lower() == "python":
            return await self._execute_local(f"python3 -c '{code}'", 30)
        elif language.lower() == "bash":
            return await self._execute_local(code, 30)
        else:
            return f"Error: Local execution for language '{language}' is not supported"

    def _format_code_result(self, result) -> str:
        """格式化代码执行结果"""
        lines = []
        if hasattr(result, "result") and result.result:
            for item in result.result:
                lines.append(item.text if hasattr(item, "text") else str(item))
        if hasattr(result, "logs") and result.logs:
            if hasattr(result.logs, "stdout") and result.logs.stdout:
                for line in result.logs.stdout:
                    lines.append(line.text if hasattr(line, "text") else str(line))
            if hasattr(result.logs, "stderr") and result.logs.stderr:
                for line in result.logs.stderr:
                    lines.append(f"[stderr] {line.text if hasattr(line, 'text') else str(line)}")
        return "\n".join(lines) if lines else "(no output)"

    async def shutdown(self):
        """关闭执行器"""
        await self.manager.shutdown()
