"""
沙箱配置模块
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class SandboxConfig:
    """沙箱配置"""
    enabled: bool = True
    provider: str = "opensandbox"  # opensandbox | local
    image: str = "opensandbox/code-interpreter:v1.0.2"
    max_pool_size: int = 3
    timeout: int = 600
    allowed_directories: List[str] = field(default_factory=lambda: ["workspace/"])
    network_enabled: bool = True
    egress_policy: str = "allow"  # allow | deny | restricted

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "SandboxConfig":
        """从字典创建配置"""
        if not config:
            return cls()

        network = config.get("network", {})
        return cls(
            enabled=config.get("enabled", True),
            provider=config.get("provider", "opensandbox"),
            image=config.get("image", "opensandbox/code-interpreter:v1.0.2"),
            max_pool_size=config.get("max_pool_size", 3),
            timeout=config.get("timeout", 600),
            allowed_directories=config.get("allowed_directories", ["workspace/"]),
            network_enabled=network.get("enabled", True),
            egress_policy=network.get("egress_policy", "allow"),
        )
