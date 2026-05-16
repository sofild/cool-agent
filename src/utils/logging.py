import os
import logging
from pathlib import Path


def setup_logging(level: str = None):
    if level is None:
        level = os.getenv("LOG_LEVEL", "info").upper()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "agent.log", encoding='utf-8')
        ]
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
