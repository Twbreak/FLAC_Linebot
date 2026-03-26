"""Shared logging configuration for the application."""

import logging
import os
from logging.handlers import TimedRotatingFileHandler


def setup_logging() -> logging.Logger:
    """Configure application logging with 30-day retention."""
    logger = logging.getLogger()
    if getattr(setup_logging, "_configured", False):
        return logger

    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "flac_linebot.log")

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    setup_logging._configured = True
    return logger
