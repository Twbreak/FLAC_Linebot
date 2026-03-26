"""Tests for shared logging configuration."""

from logging.handlers import TimedRotatingFileHandler
from unittest.mock import patch

from app_logging import setup_logging


@patch("app_logging.os.makedirs")
def test_setup_logging_configures_30_day_rotation(mock_makedirs):
    setup_logging._configured = False

    logger = setup_logging()

    file_handlers = [
        handler for handler in logger.handlers
        if isinstance(handler, TimedRotatingFileHandler)
    ]

    assert file_handlers
    assert file_handlers[-1].backupCount == 30
