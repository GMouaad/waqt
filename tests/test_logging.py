"""Tests for the centralized logging module."""

import logging
import os
import tempfile
from unittest.mock import patch

import pytest


class TestLoggingModule:
    """Test cases for waqt.logging module."""

    def test_get_log_level_default(self):
        """Test default log level is INFO."""
        from waqt.logging import get_log_level

        with patch.dict(os.environ, {}, clear=True):
            # Remove WAQT_LOG_LEVEL if present
            os.environ.pop("WAQT_LOG_LEVEL", None)
            level = get_log_level()
            assert level == logging.INFO

    def test_get_log_level_debug(self):
        """Test DEBUG log level from environment."""
        from waqt.logging import get_log_level

        with patch.dict(os.environ, {"WAQT_LOG_LEVEL": "DEBUG"}):
            level = get_log_level()
            assert level == logging.DEBUG

    def test_get_log_level_warning(self):
        """Test WARNING log level from environment."""
        from waqt.logging import get_log_level

        with patch.dict(os.environ, {"WAQT_LOG_LEVEL": "WARNING"}):
            level = get_log_level()
            assert level == logging.WARNING

    def test_get_log_level_case_insensitive(self):
        """Test log level is case insensitive."""
        from waqt.logging import get_log_level

        with patch.dict(os.environ, {"WAQT_LOG_LEVEL": "error"}):
            level = get_log_level()
            assert level == logging.ERROR

    def test_get_log_level_invalid_falls_back_to_info(self):
        """Test invalid log level falls back to INFO."""
        from waqt.logging import get_log_level

        with patch.dict(os.environ, {"WAQT_LOG_LEVEL": "INVALID"}):
            level = get_log_level()
            assert level == logging.INFO

    def test_get_logs_directory_default(self):
        """Test logs directory is created inside data directory."""
        from waqt.logging import get_logs_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                logs_dir = get_logs_directory()
                assert logs_dir == os.path.join(tmpdir, "logs")
                assert os.path.isdir(logs_dir)

    def test_get_logs_directory_creates_if_not_exists(self):
        """Test logs directory is created if it doesn't exist."""
        from waqt.logging import get_logs_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "new_data_dir")
            with patch.dict(os.environ, {"WAQT_DATA_DIR": data_dir}):
                logs_dir = get_logs_directory()
                assert os.path.isdir(logs_dir)

    def test_setup_logger_creates_file_handler(self):
        """Test setup_logger creates a file handler."""
        from waqt.logging import setup_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                # Clear any existing handlers
                logger_name = "test_file_logger"
                test_logger = logging.getLogger(logger_name)
                test_logger.handlers.clear()

                logger = setup_logger(logger_name, "test.log")

                # Check file was created
                log_file = os.path.join(tmpdir, "logs", "test.log")
                assert os.path.exists(log_file)

                # Write a log and verify it appears
                logger.info("Test message")

                with open(log_file) as f:
                    content = f.read()
                    assert "Test message" in content

                # Cleanup
                logger.handlers.clear()

    def test_setup_logger_console_output(self):
        """Test setup_logger adds console handler when requested."""
        from waqt.logging import setup_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                logger_name = "test_console_logger"
                test_logger = logging.getLogger(logger_name)
                test_logger.handlers.clear()

                logger = setup_logger(
                    logger_name, "test_console.log", console_output=True
                )

                # Should have 2 handlers: file + console
                assert len(logger.handlers) == 2

                # Cleanup
                logger.handlers.clear()

    def test_setup_logger_avoids_duplicate_handlers(self):
        """Test setup_logger does not add duplicate handlers."""
        from waqt.logging import setup_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                logger_name = "test_duplicate_logger"
                test_logger = logging.getLogger(logger_name)
                test_logger.handlers.clear()

                # Call setup twice
                logger1 = setup_logger(logger_name, "test_dup.log")
                logger2 = setup_logger(logger_name, "test_dup.log")

                # Should be the same logger with same handlers
                assert logger1 is logger2
                assert len(logger1.handlers) == 1

                # Cleanup
                logger1.handlers.clear()

    def test_get_flask_logger(self):
        """Test get_flask_logger returns correctly configured logger."""
        from waqt.logging import get_flask_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                # Clear existing handlers
                flask_logger = logging.getLogger("waqt.flask")
                flask_logger.handlers.clear()

                logger = get_flask_logger()
                assert logger.name == "waqt.flask"

                # Cleanup
                logger.handlers.clear()

    def test_get_cli_logger_with_verbose(self):
        """Test get_cli_logger adds console output when verbose."""
        from waqt.logging import get_cli_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                # Clear existing handlers
                cli_logger = logging.getLogger("waqt.cli")
                cli_logger.handlers.clear()

                logger = get_cli_logger(verbose=True)
                assert logger.name == "waqt.cli"

                # Should have file + console handlers
                assert len(logger.handlers) == 2

                # Cleanup
                logger.handlers.clear()

    def test_get_mcp_logger(self):
        """Test get_mcp_logger returns correctly configured logger."""
        from waqt.logging import get_mcp_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                # Clear existing handlers
                mcp_logger = logging.getLogger("waqt.mcp")
                mcp_logger.handlers.clear()

                logger = get_mcp_logger()
                assert logger.name == "waqt.mcp"

                # Cleanup
                logger.handlers.clear()

    def test_get_app_logger(self):
        """Test get_app_logger returns correctly configured logger."""
        from waqt.logging import get_app_logger

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WAQT_DATA_DIR": tmpdir}):
                # Clear existing handlers
                app_logger = logging.getLogger("waqt")
                app_logger.handlers.clear()

                logger = get_app_logger()
                assert logger.name == "waqt"

                # Cleanup
                logger.handlers.clear()
