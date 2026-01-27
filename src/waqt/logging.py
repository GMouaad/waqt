"""Centralized logging configuration for waqt application.

This module provides a unified logging system with:
- Interface-specific loggers (Flask, CLI, MCP)
- Rotating file handlers to prevent unbounded log growth
- Environment variable configuration for log level
- Logs stored in <WAQT_DATA_DIR>/logs/
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

import platformdirs

# Log format constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default settings
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3


def get_log_level() -> int:
    """Get log level from environment variable.

    Supports: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Default: INFO
    """
    level_name = os.environ.get("WAQT_LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def get_logs_directory() -> str:
    """Get the logs directory path.

    Returns path to logs folder inside the data directory.
    Uses WAQT_DATA_DIR environment variable if set, otherwise
    uses platform-specific user data directory.
    """
    custom_data_dir = os.environ.get("WAQT_DATA_DIR")
    if custom_data_dir:
        base_dir = os.path.abspath(custom_data_dir)
    else:
        base_dir = platformdirs.user_data_dir("waqt", "GMouaad")

    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[int] = None,
    console_output: bool = False,
) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name (e.g., 'waqt.flask')
        log_file: Log filename (created in logs directory)
        level: Log level (defaults to WAQT_LOG_LEVEL env var or INFO)
        console_output: Also output to console if True

    Returns:
        Configured logger instance.
    """
    if level is None:
        level = get_log_level()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # File handler with rotation
    if log_file:
        logs_dir = get_logs_directory()
        file_path = os.path.join(logs_dir, log_file)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# Pre-configured loggers for each interface
def get_flask_logger() -> logging.Logger:
    """Get logger for Flask web interface."""
    return setup_logger("waqt.flask", "flask.log")


def get_cli_logger(verbose: bool = False) -> logging.Logger:
    """Get logger for CLI interface."""
    return setup_logger("waqt.cli", "cli.log", console_output=verbose)


def get_mcp_logger() -> logging.Logger:
    """Get logger for MCP server."""
    return setup_logger("waqt.mcp", "mcp.log")


def get_app_logger() -> logging.Logger:
    """Get general application logger."""
    return setup_logger("waqt", "app.log")
