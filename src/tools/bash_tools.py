import subprocess
from typing import Dict, Any


class BashTools:
    """命令执行工具"""

    bash_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"},
            "timeout": {"type": "integer", "description": "超时时间（秒）", "minimum": 1, "maximum": 300}
        },
        "required": ["command"]
    }

    def bash(self, input_data: Dict[str, Any]) -> str:
        """执行命令"""
        command = input_data["command"]
        timeout = input_data.get("timeout", 30)

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
