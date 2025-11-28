"""Centralised logging helpers for Lootmore desktop client."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from typing import Optional

from config import get_appdata_dir

LOG_FILENAME = "lootmore.log"
MAX_BYTES = 512_000
BACKUP_COUNT = 3


def _ensure_log_dir() -> Path:
    log_dir = get_appdata_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(name: str = "lootmore", level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger that writes to AppData and stdout."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_path = _ensure_log_dir() / LOG_FILENAME
    file_handler = RotatingFileHandler(log_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.propagate = False
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return setup_logging(name or "lootmore")
