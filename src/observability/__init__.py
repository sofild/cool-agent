"""
可观测性模块统一入口

提供链路追踪(Tracing)、指标(Metrics)、结构化日志(Logging)的初始化和管理
"""

from typing import Dict, Any, Optional

from .tracing import TracingManager
from .metrics import MetricsManager
from .logging import StructuredLogging


class ObservabilityManager:
    """可观测性管理器"""

    _instance: Optional["ObservabilityManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Dict[str, Any] = None):
        if self._initialized:
            return

        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        self.tracing: Optional[TracingManager] = None
        self.metrics: Optional[MetricsManager] = None
        self.logging: Optional[StructuredLogging] = None

        self._initialized = True

    def initialize(self, console_output: bool = True):
        """初始化所有可观测性组件

        Args:
            console_output: 是否将日志输出到终端
        """
        if not self.enabled:
            return

        self.logging = StructuredLogging(self.config.get("logs", {}))
        self.logging.setup(console_output=console_output)

        self.tracing = TracingManager(self.config.get("traces", {}))
        self.tracing.setup()

        self.metrics = MetricsManager(self.config.get("metrics", {}))
        self.metrics.setup()

    def shutdown(self):
        """关闭所有可观测性组件"""
        if self.tracing:
            self.tracing.shutdown()
        if self.metrics:
            self.metrics.shutdown()

    def get_tracer(self, name: str):
        """获取 tracer"""
        if self.tracing:
            return self.tracing.get_tracer(name)
        return None

    def get_meter(self, name: str):
        """获取 meter"""
        if self.metrics:
            return self.metrics.get_meter(name)
        return None

    def get_logger(self, name: str):
        """获取结构化 logger"""
        if self.logging:
            return self.logging.get_logger(name)
        import logging
        return logging.getLogger(name)


# 全局可观测性实例
_observability: Optional[ObservabilityManager] = None


def setup_observability(config: Dict[str, Any] = None, console_output: bool = True) -> ObservabilityManager:
    """设置可观测性

    Args:
        config: 可观测性配置
        console_output: 是否将日志输出到终端，CLI 交互模式下建议设为 False
    """
    global _observability
    _observability = ObservabilityManager(config)
    _observability.initialize(console_output=console_output)
    return _observability


def get_observability() -> Optional[ObservabilityManager]:
    """获取可观测性实例"""
    return _observability


def get_tracer(name: str):
    """获取 tracer 快捷方法，始终返回可用的 tracer（NoOp 兜底）"""
    if _observability:
        tracer = _observability.get_tracer(name)
        if tracer is not None:
            return tracer
    from opentelemetry.trace import NoOpTracer
    return NoOpTracer()


def get_meter(name: str):
    """获取 meter 快捷方法"""
    if _observability:
        return _observability.get_meter(name)
    return None


def get_logger(name: str):
    """获取 logger 快捷方法"""
    if _observability:
        return _observability.get_logger(name)
    import logging
    return logging.getLogger(name)
