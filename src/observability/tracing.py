"""
链路追踪管理模块

基于 OpenTelemetry 实现分布式链路追踪，支持 OTLP 导出到 Jaeger/Grafana/阿里云等后端
"""

import os
import socket
from typing import Dict, Any, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode


def _is_endpoint_reachable(endpoint: str, timeout: float = 1.0) -> bool:
    """检查 OTLP endpoint 是否可达"""
    try:
        host, port = endpoint.replace("http://", "").replace("https://", "").split(":")
        port = int(port)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


class TracingManager:
    """链路追踪管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.exporter_type = self.config.get("exporter", "otlp")
        self.endpoint = self.config.get("endpoint", "http://localhost:4317")
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "cool-agent")

        self._provider: Optional[TracerProvider] = None
        self._tracers: Dict[str, trace.Tracer] = {}

    def setup(self):
        """初始化链路追踪"""
        if not self.enabled:
            return

        resource = Resource.create({SERVICE_NAME: self.service_name})
        self._provider = TracerProvider(resource=resource)

        exporter = self._create_exporter()
        if exporter:
            processor = BatchSpanProcessor(exporter)
            self._provider.add_span_processor(processor)

        trace.set_tracer_provider(self._provider)

    def _create_exporter(self):
        """创建 Span 导出器，OTLP 不可达时静默丢弃"""
        if self.exporter_type in ("otlp", "jaeger"):
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", self.endpoint)
            if _is_endpoint_reachable(endpoint):
                return OTLPSpanExporter(endpoint=endpoint)
            import logging
            logging.getLogger("observability.tracing").warning(
                f"OTLP endpoint {endpoint} is not reachable. "
                f"Traces will be silently dropped."
            )
            return None
        elif self.exporter_type == "console":
            return ConsoleSpanExporter()
        return None

    def get_tracer(self, name: str) -> trace.Tracer:
        """获取 tracer"""
        if name not in self._tracers:
            self._tracers[name] = trace.get_tracer(name)
        return self._tracers[name]

    def shutdown(self):
        """关闭链路追踪"""
        if self._provider:
            self._provider.shutdown()


class SpanContext:
    """Span 上下文管理器（用于 with 语句）"""

    def __init__(self, tracer: trace.Tracer, name: str, kind: trace.SpanKind = trace.SpanKind.INTERNAL, attributes: Dict[str, Any] = None):
        self.tracer = tracer
        self.name = name
        self.kind = kind
        self.attributes = attributes or {}
        self.span = None

    def __enter__(self):
        self.span = self.tracer.start_span(self.name, kind=self.kind, attributes=self.attributes)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_val:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            self.span.end()


def set_span_attribute(span, key: str, value: Any):
    """安全地设置 span 属性"""
    if span and span.is_recording():
        if value is not None:
            span.set_attribute(key, value)


def set_span_attributes(span, attributes: Dict[str, Any]):
    """安全地批量设置 span 属性"""
    if span and span.is_recording():
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)


def add_span_event(span, name: str, attributes: Dict[str, Any] = None):
    """安全地添加 span 事件"""
    if span and span.is_recording():
        span.add_event(name, attributes or {})


def record_exception(span, exception: Exception):
    """安全地记录异常到 span"""
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))
