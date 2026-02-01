"""Unit tests for the process_manager module."""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from waqt import process_manager


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Set up a temporary data directory for tests."""
    data_dir = tmp_path / "waqt_data"
    data_dir.mkdir()
    monkeypatch.setenv("WAQT_DATA_DIR", str(data_dir))
    return data_dir


class TestGetDataDir:
    """Tests for get_data_dir function."""

    def test_uses_env_var_when_set(self, tmp_path, monkeypatch):
        """Test that WAQT_DATA_DIR env var is honored."""
        custom_dir = tmp_path / "custom_waqt"
        monkeypatch.setenv("WAQT_DATA_DIR", str(custom_dir))
        result = process_manager.get_data_dir()
        assert result == custom_dir

    def test_uses_platformdirs_when_no_env_var(self, monkeypatch):
        """Test that platformdirs is used when env var not set."""
        monkeypatch.delenv("WAQT_DATA_DIR", raising=False)
        result = process_manager.get_data_dir()
        assert "waqt" in str(result).lower()


class TestStateFileOperations:
    """Tests for state file read/write operations."""

    def test_read_state_file_not_exists(self, temp_data_dir):
        """Test reading non-existent state file returns None."""
        result = process_manager.read_state_file()
        assert result is None

    def test_read_state_file_valid(self, temp_data_dir):
        """Test reading valid state file."""
        state_file = temp_data_dir / "waqt_server.json"
        state = {"pid": 123, "port": 5555}
        state_file.write_text(json.dumps(state))
        result = process_manager.read_state_file()
        assert result == state

    def test_read_state_file_invalid_json(self, temp_data_dir):
        """Test reading invalid JSON returns None."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text("not valid json {{{")
        result = process_manager.read_state_file()
        assert result is None

    def test_write_state_file(self, temp_data_dir):
        """Test writing state file."""
        state = {"pid": 456, "port": 8080, "host": "127.0.0.1"}
        process_manager.write_state_file(state)
        state_file = temp_data_dir / "waqt_server.json"
        assert state_file.exists()
        saved = json.loads(state_file.read_text())
        assert saved == state

    def test_cleanup_state_files(self, temp_data_dir):
        """Test cleanup removes state file."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text('{"pid": 123}')
        assert state_file.exists()
        process_manager.cleanup_state_files()
        assert not state_file.exists()

    def test_cleanup_state_files_no_file(self, temp_data_dir):
        """Test cleanup when no file exists doesn't error."""
        process_manager.cleanup_state_files()  # Should not raise


class TestIsProcessRunning:
    """Tests for is_process_running function."""

    def test_invalid_pid_zero(self):
        """Test that PID 0 returns False."""
        assert process_manager.is_process_running(0) is False

    def test_invalid_pid_negative(self):
        """Test that negative PID returns False."""
        assert process_manager.is_process_running(-1) is False

    @pytest.mark.skipif(not process_manager.HAS_PSUTIL, reason="psutil not installed")
    def test_with_psutil_available(self):
        """Test using psutil when available."""
        import psutil

        with patch.object(psutil, "pid_exists", return_value=True) as mock:
            result = process_manager.is_process_running(123)
            mock.assert_called_once_with(123)
            assert result is True

    def test_without_psutil_unix(self):
        """Test Unix fallback when psutil not available."""
        with patch.object(process_manager, "HAS_PSUTIL", False):
            with patch("sys.platform", "linux"):
                with patch("os.kill") as mock_kill:
                    result = process_manager.is_process_running(123)
                    mock_kill.assert_called_once_with(123, 0)
                    assert result is True

    def test_without_psutil_unix_not_running(self):
        """Test Unix fallback when process not running."""
        with patch.object(process_manager, "HAS_PSUTIL", False):
            with patch("sys.platform", "linux"):
                with patch("os.kill", side_effect=ProcessLookupError):
                    result = process_manager.is_process_running(123)
                    assert result is False

    def test_without_psutil_windows(self):
        """Test Windows fallback using tasklist."""
        with patch.object(process_manager, "HAS_PSUTIL", False):
            with patch("sys.platform", "win32"):
                mock_result = MagicMock()
                mock_result.stdout = "python.exe    123    Console"
                with patch("subprocess.run", return_value=mock_result):
                    result = process_manager.is_process_running(123)
                    assert result is True


class TestIsOurProcess:
    """Tests for is_our_process function."""

    def test_invalid_pid(self):
        """Test that invalid PID returns False."""
        assert process_manager.is_our_process(0) is False
        assert process_manager.is_our_process(-1) is False

    @pytest.mark.skipif(not process_manager.HAS_PSUTIL, reason="psutil not installed")
    def test_with_psutil_waqt_process(self):
        """Test psutil path identifies waqt process."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.cmdline.return_value = ["python", "-m", "waqt.wsgi_server"]
        with patch.object(psutil, "Process", return_value=mock_proc):
            result = process_manager.is_our_process(123)
            assert result is True

    @pytest.mark.skipif(not process_manager.HAS_PSUTIL, reason="psutil not installed")
    def test_with_psutil_other_process(self):
        """Test psutil path identifies non-waqt process."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.cmdline.return_value = ["nginx", "-g", "daemon off"]
        with patch.object(psutil, "Process", return_value=mock_proc):
            result = process_manager.is_our_process(123)
            assert result is False

    def test_fallback_no_state_file(self, temp_data_dir):
        """Test fallback when no state file exists."""
        with patch.object(process_manager, "HAS_PSUTIL", False):
            result = process_manager.is_our_process(123)
            assert result is False

    def test_fallback_pid_mismatch(self, temp_data_dir):
        """Test fallback when PID doesn't match state file."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text(
            json.dumps({"pid": 456, "port": 5555, "host": "127.0.0.1"})
        )
        with patch.object(process_manager, "HAS_PSUTIL", False):
            result = process_manager.is_our_process(123)
            assert result is False

    def test_fallback_success(self, temp_data_dir):
        """Test fallback when all conditions met."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text(
            json.dumps({"pid": 123, "port": 5555, "host": "127.0.0.1"})
        )
        with patch.object(process_manager, "HAS_PSUTIL", False):
            with patch.object(process_manager, "is_process_running", return_value=True):
                with patch.object(process_manager, "is_port_in_use", return_value=True):
                    result = process_manager.is_our_process(123)
                    assert result is True


class TestIsPortInUse:
    """Tests for is_port_in_use function."""

    def test_port_available(self):
        """Test detecting available port."""
        # Use a high port number unlikely to be in use
        result = process_manager.is_port_in_use("127.0.0.1", 59999)
        assert result is False

    def test_port_in_use(self):
        """Test detecting port in use."""
        import socket

        # Bind to a port to make it in use
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 59998))
            result = process_manager.is_port_in_use("127.0.0.1", 59998)
            assert result is True


class TestGetUptime:
    """Tests for get_uptime function."""

    def test_none_input(self):
        """Test with None input."""
        assert process_manager.get_uptime(None) is None

    def test_invalid_format(self):
        """Test with invalid timestamp format."""
        assert process_manager.get_uptime("not a timestamp") is None

    def test_seconds(self):
        """Test uptime in seconds."""
        started = (datetime.now() - timedelta(seconds=30)).isoformat()
        result = process_manager.get_uptime(started)
        assert result.endswith("s")
        assert "30" in result or "29" in result or "31" in result

    def test_minutes(self):
        """Test uptime in minutes."""
        started = (datetime.now() - timedelta(minutes=15)).isoformat()
        result = process_manager.get_uptime(started)
        assert result == "15m"

    def test_hours_and_minutes(self):
        """Test uptime in hours and minutes."""
        started = (datetime.now() - timedelta(hours=2, minutes=30)).isoformat()
        result = process_manager.get_uptime(started)
        assert result == "2h 30m"


class TestStartBackgroundServer:
    """Tests for start_background_server error cases."""

    def test_process_exits_immediately(self, temp_data_dir):
        """Test when spawned process exits immediately."""
        mock_process = MagicMock()
        mock_process.pid = 99999

        with patch.object(process_manager, "is_port_in_use", return_value=False):
            with patch("subprocess.Popen", return_value=mock_process):
                with patch.object(
                    process_manager, "is_process_running", return_value=False
                ):
                    result = process_manager.start_background_server("127.0.0.1", 5555)
                    assert result["success"] is False
                    assert "exited immediately" in result["message"]

    def test_popen_exception(self, temp_data_dir):
        """Test when Popen raises an exception."""
        with patch.object(process_manager, "is_port_in_use", return_value=False):
            with patch("subprocess.Popen", side_effect=OSError("spawn failed")):
                result = process_manager.start_background_server("127.0.0.1", 5555)
                assert result["success"] is False
                assert "Failed to start" in result["message"]


class TestStopServer:
    """Tests for stop_server error cases."""

    def test_stop_process_timeout(self, temp_data_dir):
        """Test when process doesn't stop within timeout."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text(
            json.dumps({"pid": 123, "port": 5555, "host": "127.0.0.1"})
        )

        with patch.object(
            process_manager, "is_process_running", return_value=True
        ):  # Always running
            with patch.object(process_manager, "is_our_process", return_value=True):
                with patch("os.kill"):
                    with patch("time.sleep"):
                        result = process_manager.stop_server(force=False)
                        assert result["success"] is False
                        assert "did not stop" in result["message"]
                        # State file should NOT be cleaned up
                        assert state_file.exists()

    def test_stop_force_timeout(self, temp_data_dir):
        """Test force stop when process still doesn't terminate."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text(
            json.dumps({"pid": 123, "port": 5555, "host": "127.0.0.1"})
        )

        with patch.object(process_manager, "is_process_running", return_value=True):
            with patch.object(process_manager, "is_our_process", return_value=True):
                with patch("os.kill"):
                    with patch("time.sleep"):
                        result = process_manager.stop_server(force=True)
                        assert result["success"] is False
                        assert "forcibly terminate" in result["message"]

    def test_stop_windows_taskkill_failure(self, temp_data_dir):
        """Test Windows taskkill returning error."""
        state_file = temp_data_dir / "waqt_server.json"
        state_file.write_text(
            json.dumps({"pid": 123, "port": 5555, "host": "127.0.0.1"})
        )

        with patch.object(process_manager, "is_process_running", return_value=True):
            with patch.object(process_manager, "is_our_process", return_value=True):
                with patch("sys.platform", "win32"):
                    mock_result = MagicMock()
                    mock_result.returncode = 1
                    mock_result.stdout = ""
                    mock_result.stderr = "Access denied"
                    with patch("subprocess.run", return_value=mock_result):
                        result = process_manager.stop_server()
                        assert result["success"] is False
                        assert "taskkill" in result["message"]
                        assert "Access denied" in result["message"]
