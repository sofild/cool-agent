from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class PermissionMode(Enum):
    """权限模式"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class PermissionRule:
    """权限规则"""
    pattern: str
    action: str
    level: str = "read"


class PermissionManager:
    """权限管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.mode = PermissionMode(config.get("mode", "ask")) if config else PermissionMode.ASK
        self.rules: List[PermissionRule] = []

        if config and "rules" in config:
            for rule in config["rules"]:
                self.rules.append(PermissionRule(
                    pattern=rule["pattern"],
                    action=rule["action"],
                    level=rule.get("level", "read")
                ))

    def check_permission(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """检查权限"""
        import fnmatch

        for rule in self.rules:
            if fnmatch.fnmatch(tool_name, rule.pattern):
                if rule.action == "deny":
                    return False
                elif rule.action == "ask":
                    raise PermissionError(f"Permission required for: {tool_name}")

        return True

    def add_rule(self, pattern: str, action: str, level: str = "read"):
        """添加权限规则"""
        self.rules.append(PermissionRule(pattern, action, level))
