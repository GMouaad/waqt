"""Tests for the UI background process management CLI commands."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from waqt.cli import cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Set up a temporary data directory for tests."""
    data_dir = tmp_path / "waqt_data"
    data_dir.mkdir()
    monkeypatch.setenv("WAQT_DATA_DIR", str(data_dir))
    return data_dir


class TestUIStatus:
    """Tests for 'waqt ui status' command."""

    def test_status_not_running(self, runner, temp_data_dir):
        """Test status when no server is running."""
        result = runner.invoke(cli, ["ui", "status"])
        assert result.exit_code == 0
        assert "not running" in result.output.lower()

    def test_status_running(self, runner, temp_data_dir):
        """Test status when server is running (mocked)."""
        # Create a state file
        state_file = temp_data_dir / "waqt_server.json"
        state = {
            "pid": 12345,
            "port": 5555,
            "host": "127.0.0.1",
            "started_at": "2026-01-01T10:00:00",
        }
        state_file.write_text(json.dumps(state))

        with patch("waqt.process_manager.is_process_running", return_value=True):
            with patch("waqt.process_manager.is_our_process", return_value=True):
                result = runner.invoke(cli, ["ui", "status"])
                assert result.exit_code == 0
                assert "running" in result.output.lower()
                assert "12345" in result.output
                assert "5555" in result.output

    def test_status_stale_file_cleanup(self, runner, temp_data_dir):
        """Test that stale state files are cleaned up."""
        # Create a stale state file
        state_file = temp_data_dir / "waqt_server.json"
        state = {"pid": 99999, "port": 5555, "host": "127.0.0.1"}
        state_file.write_text(json.dumps(state))

        with patch("waqt.process_manager.is_process_running", return_value=False):
            result = runner.invoke(cli, ["ui", "status"])
            assert result.exit_code == 0
            assert "not running" in result.output.lower()
            # State file should be cleaned up
            assert not state_file.exists()


class TestUIStart:
    """Tests for 'waqt ui start' command."""

    def test_start_already_running(self, runner, temp_data_dir):
        """Test start when server is already running."""
        # Create a state file indicating server is running
        state_file = temp_data_dir / "waqt_server.json"
        state = {"pid": 12345, "port": 5555, "host": "127.0.0.1"}
        state_file.write_text(json.dumps(state))

        with patch("waqt.process_manager.is_process_running", return_value=True):
            with patch("waqt.process_manager.is_our_process", return_value=True):
                result = runner.invoke(cli, ["ui", "start"])
                assert result.exit_code == 1
                assert "already running" in result.output.lower()

    def test_start_port_in_use(self, runner, temp_data_dir):
        """Test start when port is already in use."""
        with patch("waqt.process_manager.is_port_in_use", return_value=True):
            result = runner.invoke(cli, ["ui", "start"])
            assert result.exit_code == 1
            assert "already in use" in result.output.lower()

    def test_start_success(self, runner, temp_data_dir):
        """Test successful server start."""
        mock_process = MagicMock()
        mock_process.pid = 54321

        with patch("waqt.process_manager.is_port_in_use", return_value=False):
            with patch("subprocess.Popen", return_value=mock_process):
                with patch(
                    "waqt.process_manager.is_process_running", return_value=True
                ):
                    result = runner.invoke(cli, ["ui", "start"])
                    assert result.exit_code == 0
                    assert "started" in result.output.lower()
                    assert "54321" in result.output

                    # State file should be created
                    state_file = temp_data_dir / "waqt_server.json"
                    assert state_file.exists()
                    state = json.loads(state_file.read_text())
                    assert state["pid"] == 54321


class TestUIStop:
    """Tests for 'waqt ui stop' command."""

    def test_stop_not_running(self, runner, temp_data_dir):
        """Test stop when no server is running."""
        result = runner.invoke(cli, ["ui", "stop"])
        assert result.exit_code == 1
        assert "not running" in result.output.lower()

    def test_stop_success_unix(self, runner, temp_data_dir):
        """Test successful server stop on Unix."""
        # Create a state file
        state_file = temp_data_dir / "waqt_server.json"
        state = {"pid": 12345, "port": 5555, "host": "127.0.0.1"}
        state_file.write_text(json.dumps(state))

        with patch("waqt.process_manager.is_process_running") as mock_running:
            # First call: running, subsequent calls: not running
            mock_running.side_effect = [True, True, False]
            with patch("waqt.process_manager.is_our_process", return_value=True):
                with patch("os.kill") as mock_kill:
                    with patch("sys.platform", "linux"):
                        result = runner.invoke(cli, ["ui", "stop"])
                        assert result.exit_code == 0
                        assert "stopped" in result.output.lower()
                        # State file should be cleaned up
                        assert not state_file.exists()

    def test_stop_with_force(self, runner, temp_data_dir):
        """Test stop with --force flag."""
        # Create a state file
        state_file = temp_data_dir / "waqt_server.json"
        state = {"pid": 12345, "port": 5555, "host": "127.0.0.1"}
        state_file.write_text(json.dumps(state))

        with patch("waqt.process_manager.is_process_running") as mock_running:
            mock_running.side_effect = [True, True, False]
            with patch("waqt.process_manager.is_our_process", return_value=True):
                with patch("os.kill") as mock_kill:
                    result = runner.invoke(cli, ["ui", "stop", "--force"])
                    assert result.exit_code == 0
                    assert "stopped" in result.output.lower()


class TestUIHelp:
    """Tests for UI command help text."""

    def test_ui_help(self, runner):
        """Test 'waqt ui --help' shows all subcommands."""
        result = runner.invoke(cli, ["ui", "--help"])
        assert result.exit_code == 0
        assert "start" in result.output
        assert "stop" in result.output
        assert "status" in result.output

    def test_ui_start_help(self, runner):
        """Test 'waqt ui start --help'."""
        result = runner.invoke(cli, ["ui", "start", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--host" in result.output

    def test_ui_stop_help(self, runner):
        """Test 'waqt ui stop --help' has platform-neutral text."""
        result = runner.invoke(cli, ["ui", "stop", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output
        # Should NOT contain platform-specific signal names
        assert "SIGKILL" not in result.output
        assert "SIGTERM" not in result.output
