"""
指标采集管理模块

基于 OpenTelemetry 实现性能指标采集，支持 Counter、Histogram、Gauge 等类型
"""

import os
import socket
from typing import Dict, Any, Optional

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter


def _is_endpoint_reachable(endpoint: str, timeout: float = 1.0) -> bool:
    """检查 OTLP endpoint 是否可达"""
    try:
        host, port = endpoint.replace("http://", "").replace("https://", "").split(":")
        port = int(port)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


class MetricsManager:
    """指标管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.exporter_type = self.config.get("exporter", "otlp")
        self.endpoint = self.config.get("endpoint", "http://localhost:4317")
        self.export_interval = self.config.get("export_interval", 60000)
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "cool-agent")

        self._provider: Optional[MeterProvider] = None
        self._meters: Dict[str, metrics.Meter] = {}

        self._counters: Dict[str, metrics.Counter] = {}
        self._histograms: Dict[str, metrics.Histogram] = {}
        self._gauges: Dict[str, metrics.ObservableGauge] = {}

    def setup(self):
        """初始化指标采集"""
        if not self.enabled:
            return

        resource = Resource.create({SERVICE_NAME: self.service_name})

        exporter = self._create_exporter()
        if exporter:
            reader = PeriodicExportingMetricReader(
                exporter,
                export_interval_millis=self.export_interval
            )
            self._provider = MeterProvider(resource=resource, metric_readers=[reader])
        else:
            self._provider = MeterProvider(resource=resource)

        metrics.set_meter_provider(self._provider)

    def _create_exporter(self):
        """创建指标导出器，OTLP 不可达时静默丢弃"""
        if self.exporter_type == "otlp":
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", self.endpoint)
            if _is_endpoint_reachable(endpoint):
                return OTLPMetricExporter(endpoint=endpoint)
            import logging
            logging.getLogger("observability.metrics").warning(
                f"OTLP endpoint {endpoint} is not reachable. "
                f"Metrics will be silently dropped."
            )
            return None
        elif self.exporter_type == "console":
            return ConsoleMetricExporter()
        return None

    def get_meter(self, name: str) -> metrics.Meter:
        """获取 meter"""
        if name not in self._meters:
            self._meters[name] = metrics.get_meter(name)
        return self._meters[name]

    def get_counter(self, meter: metrics.Meter, name: str, description: str = "", unit: str = "1") -> metrics.Counter:
        """获取或创建 Counter"""
        key = f"{meter._instrumentation_scope.name}.{name}"
        if key not in self._counters:
            self._counters[key] = meter.create_counter(name, description=description, unit=unit)
        return self._counters[key]

    def get_histogram(self, meter: metrics.Meter, name: str, description: str = "", unit: str = "ms") -> metrics.Histogram:
        """获取或创建 Histogram"""
        key = f"{meter._instrumentation_scope.name}.{name}"
        if key not in self._histograms:
            self._histograms[key] = meter.create_histogram(name, description=description, unit=unit)
        return self._histograms[key]

    def shutdown(self):
        """关闭指标采集"""
        if self._provider:
            self._provider.shutdown()


class AgentMetrics:
    """Agent 专用指标封装"""

    def __init__(self, metrics_manager: MetricsManager):
        self.metrics_manager = metrics_manager
        if not metrics_manager or not metrics_manager.enabled:
            self.meter = None
            return

        self.meter = metrics_manager.get_meter("cool-agent")

        self.turns_total = metrics_manager.get_counter(
            self.meter, "agent.turns.total", "Agent 总回合数", "1"
        )
        self.turns_duration = metrics_manager.get_histogram(
            self.meter, "agent.turns.duration", "每回合耗时", "ms"
        )
        self.llm_prompt_tokens = metrics_manager.get_counter(
            self.meter, "agent.llm.tokens.prompt", "Prompt token 数", "1"
        )
        self.llm_completion_tokens = metrics_manager.get_counter(
            self.meter, "agent.llm.tokens.completion", "Completion token 数", "1"
        )
        self.llm_latency = metrics_manager.get_histogram(
            self.meter, "agent.llm.latency", "LLM 调用延迟", "ms"
        )
        self.tool_executions = metrics_manager.get_counter(
            self.meter, "agent.tools.executions", "工具执行次数", "1"
        )
        self.tool_latency = metrics_manager.get_histogram(
            self.meter, "agent.tools.latency", "工具执行延迟", "ms"
        )
        self.context_compressions = metrics_manager.get_counter(
            self.meter, "agent.context.compressions", "上下文压缩次数", "1"
        )
        self.errors = metrics_manager.get_counter(
            self.meter, "agent.errors", "错误次数", "1"
        )

    def record_turn(self, duration_ms: float, attributes: Dict[str, Any] = None):
        """记录回合指标"""
        if not self.meter:
            return
        attrs = attributes or {}
        self.turns_total.add(1, attrs)
        self.turns_duration.record(duration_ms, attrs)

    def record_llm_call(self, prompt_tokens: int, completion_tokens: int, latency_ms: float, model: str = ""):
        """记录 LLM 调用指标"""
        if not self.meter:
            return
        attrs = {"model": model} if model else {}
        self.llm_prompt_tokens.add(prompt_tokens, attrs)
        self.llm_completion_tokens.add(completion_tokens, attrs)
        self.llm_latency.record(latency_ms, attrs)

    def record_tool_execution(self, tool_name: str, success: bool, latency_ms: float):
        """记录工具执行指标"""
        if not self.meter:
            return
        attrs = {"tool_name": tool_name, "success": str(success).lower()}
        self.tool_executions.add(1, attrs)
        self.tool_latency.record(latency_ms, attrs)

    def record_context_compression(self):
        """记录上下文压缩"""
        if not self.meter:
            return
        self.context_compressions.add(1)

    def record_error(self, error_type: str):
        """记录错误"""
        if not self.meter:
            return
        self.errors.add(1, {"error_type": error_type})
