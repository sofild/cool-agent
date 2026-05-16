import os
from typing import List, Dict, Any
from pathlib import Path


class SandboxManager:
    """沙箱管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.enabled = config.get("enabled", True) if config else True
        self.allowed_directories = config.get("allowed_directories", ["workspace/"]) if config else ["workspace/"]
        self.denied_patterns = config.get("denied_patterns", []) if config else []

    def validate_path(self, path: str) -> bool:
        """验证路径是否在允许范围内"""
        if not self.enabled:
            return True

        path_obj = Path(path).resolve()
        allowed = False
        for allowed_dir in self.allowed_directories:
            allowed_path = Path(allowed_dir).resolve()
            try:
                path_obj.relative_to(allowed_path)
                allowed = True
                break
            except ValueError:
                continue

        if not allowed:
            return False

        for pattern in self.denied_patterns:
            if pattern in str(path_obj):
                return False

        return True

    def validate_command(self, command: str) -> bool:
        """验证命令是否安全"""
        if not self.enabled:
            return True

        dangerous_patterns = ["rm -rf", "sudo", "dd if=", "> /dev", "mkfs", "format"]
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return False

        return True
