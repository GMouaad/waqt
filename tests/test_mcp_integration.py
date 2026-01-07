"""Integration tests for MCP server executable."""

import pytest
import subprocess
import sys
import json
from pathlib import Path


def test_mcp_server_entry_point_exists():
    """Test that waqt-mcp entry point is installed."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "waqtracker"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "waqtracker" in result.stdout


def test_mcp_server_starts():
    """Test that MCP server starts without errors."""
    # Try to start the server with a timeout
    try:
        result = subprocess.run(
            ["waqt-mcp"],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except subprocess.TimeoutExpired:
        # This is expected - the server should keep running
        # waiting for MCP protocol messages on stdin
        pass
    else:
        # If it exits quickly, check it didn't error
        if result.returncode != 0:
            pytest.fail(f"MCP server exited with error: {result.stderr}")


def test_mcp_module_can_be_imported():
    """Test that the MCP server module can be imported."""
    result = subprocess.run(
        [sys.executable, "-c", "from src.waqtracker.mcp_server import mcp, main"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"


def test_mcp_server_has_tools():
    """Test that MCP server exports the expected tools."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from src.waqtracker.mcp_server import start, end, summary, list_entries, export_entries; "
            "print('success')"
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "success" in result.stdout


def test_demo_script_runs():
    """Test that the demo script runs successfully."""
    demo_path = Path(__file__).parent.parent / "demo_mcp.py"
    if demo_path.exists():
        result = subprocess.run(
            [sys.executable, str(demo_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Demo failed: {result.stderr}"
        assert "Demonstration Complete!" in result.stdout
