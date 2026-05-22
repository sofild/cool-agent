"""
结构化日志管理模块

提供 JSON 格式的结构化日志输出，与 OpenTelemetry 日志桥接
"""

import os
import sys
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "source": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.include_extra:
            extra = {}
            for key, value in record.__dict__.items():
                if key not in {
                    "name", "msg", "args", "levelname", "levelno", "pathname",
                    "filename", "module", "exc_info", "exc_text", "stack_info",
                    "lineno", "funcName", "created", "msecs", "relativeCreated",
                    "thread", "threadName", "processName", "process", "message", "asctime"
                }:
                    try:
                        json.dumps({key: value})
                        extra[key] = value
                    except (TypeError, ValueError):
                        extra[key] = str(value)
            if extra:
                log_data["extra"] = extra

        return json.dumps(log_data, ensure_ascii=False, default=str)


class StructuredLogging:
    """结构化日志管理器"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.format_type = self.config.get("format", "json")
        self.level = self.config.get("level", "info")
        self.log_file = self.config.get("file", "logs/agent.log")

    def setup(self, console_output: bool = True):
        """初始化结构化日志

        Args:
            console_output: 是否输出到终端，CLI 模式下可设为 False 避免干扰交互
        """
        if not self.enabled:
            return

        level = getattr(logging, self.level.upper(), logging.INFO)

        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        handlers = []
        if console_output:
            handlers.append(logging.StreamHandler(sys.stdout))

        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            handlers.append(file_handler)

        formatter = JSONFormatter() if self.format_type == "json" else logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in handlers:
            handler.setLevel(level)
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取 logger"""
        return logging.getLogger(name)


class AgentLogger:
    """Agent 专用日志封装"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _log(self, level: int, message: str, extra: Dict[str, Any] = None):
        """内部日志方法"""
        if extra:
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, kwargs)

    def log_turn_start(self, turn_count: int, max_turns: int):
        """记录回合开始"""
        self.info(
            f"Turn {turn_count}/{max_turns} started",
            event="turn_start",
            turn_count=turn_count,
            max_turns=max_turns,
        )

    def log_turn_end(self, turn_count: int, duration_ms: float, has_tool_calls: bool):
        """记录回合结束"""
        self.info(
            f"Turn {turn_count} completed in {duration_ms:.0f}ms",
            event="turn_end",
            turn_count=turn_count,
            duration_ms=duration_ms,
            has_tool_calls=has_tool_calls,
        )

    def log_llm_call(self, model: str, prompt_tokens: int, completion_tokens: int, latency_ms: float):
        """记录 LLM 调用"""
        self.info(
            f"LLM call to {model}: {prompt_tokens} -> {completion_tokens} tokens in {latency_ms:.0f}ms",
            event="llm_call",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )

    def log_tool_execution(self, tool_name: str, success: bool, latency_ms: float, error: str = None):
        """记录工具执行"""
        if success:
            self.info(
                f"Tool {tool_name} executed in {latency_ms:.0f}ms",
                event="tool_execution",
                tool_name=tool_name,
                success=True,
                latency_ms=latency_ms,
            )
        else:
            self.error(
                f"Tool {tool_name} failed in {latency_ms:.0f}ms: {error}",
                event="tool_execution",
                tool_name=tool_name,
                success=False,
                latency_ms=latency_ms,
                error=error,
            )

    def log_context_compression(self, level: str, messages_before: int, messages_after: int):
        """记录上下文压缩"""
        self.warning(
            f"Context compression: {level} ({messages_before} -> {messages_after} messages)",
            event="context_compression",
            level=level,
            messages_before=messages_before,
            messages_after=messages_after,
        )

    def log_error(self, error_type: str, error_message: str, recoverable: bool = False):
        """记录错误"""
        level = logging.WARNING if recoverable else logging.ERROR
        self._log(
            level,
            f"Error [{error_type}]: {error_message} (recoverable={recoverable})",
            {"event": "error", "error_type": error_type, "recoverable": recoverable},
        )
