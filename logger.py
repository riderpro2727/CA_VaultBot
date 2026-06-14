"""
CA Vault Bot - Logging Configuration
Structured logging with loguru for production.
"""
from __future__ import annotations

import sys
import logging
from typing import Optional

from loguru import logger as _logger


def setup_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Configure loguru for the application."""
    _logger.remove()

    if fmt == "json":
        _logger.add(
            sys.stdout,
            level=level,
            format=(
                '{{"time":"{time:YYYY-MM-DD HH:mm:ss.SSS}","level":"{level}",'
                '"name":"{name}","message":"{message}"}}'
            ),
            serialize=True,
        )
    else:
        _logger.add(
            sys.stdout,
            level=level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # Also intercept standard library logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = _logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            _logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("httpx", "httpcore", "telegram", "apscheduler"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str):
    """Get a named logger bound to the module."""
    return _logger.bind(name=name)
