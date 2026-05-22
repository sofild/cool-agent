import os
import logging
from pathlib import Path


def setup_logging(level: str = None, console_output: bool = True):
    """设置日志

    Args:
        level: 日志级别
        console_output: 是否输出到终端，CLI 模式下可设为 False
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "info")

    level = level.upper()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    handlers = []
    if console_output:
        handlers.append(logging.StreamHandler())
    handlers.append(logging.FileHandler(log_dir / "agent.log", encoding='utf-8'))

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
