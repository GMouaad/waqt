"""Process management for background UI server.

This module handles starting, stopping, and monitoring the Waqt web UI
as a background process. It uses PID files and state JSON for tracking,
with automatic stale file cleanup.
"""

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import platformdirs

# Optional psutil for better process verification
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_data_dir() -> Path:
    """Get the waqt data directory."""
    return Path(platformdirs.user_data_dir("waqt", "GMouaad"))


def get_state_file_path() -> Path:
    """Get the path to the state JSON file."""
    return get_data_dir() / "waqt_server.json"


def get_log_file_path() -> Path:
    """Get the path to the UI log file."""
    log_dir = get_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "ui.log"


def read_state_file() -> Optional[Dict[str, Any]]:
    """Read state from JSON file, return None if not exists or invalid."""
    state_file = get_state_file_path()
    if not state_file.exists():
        return None
    try:
        with open(state_file, "r") as f:
            return json.load(f)
    except (ValueError, OSError, json.JSONDecodeError):
        return None


def write_state_file(state: Dict[str, Any]) -> None:
    """Write state file atomically."""
    state_file = get_state_file_path()
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first for atomic operation
    fd, temp_path = tempfile.mkstemp(dir=state_file.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        # Atomic rename
        os.replace(temp_path, state_file)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def cleanup_state_files() -> None:
    """Remove all state files. Safe to call even if files don't exist."""
    state_file = get_state_file_path()
    try:
        state_file.unlink(missing_ok=True)
    except Exception:
        pass  # Best effort cleanup


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)  # Signal 0 = existence check, no actual signal sent
        return True
    except (OSError, ProcessLookupError):
        return False


def is_our_process(pid: int) -> bool:
    """Verify the PID belongs to a waqt server, not a reused PID.

    Uses psutil if available, otherwise returns True (skip check).
    """
    if not HAS_PSUTIL:
        return True  # Skip check if psutil not available

    try:
        proc = psutil.Process(pid)
        cmdline = " ".join(proc.cmdline()).lower()
        return "waqt" in cmdline
    except Exception:
        return False


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False  # Port is available
        except OSError:
            return True  # Port is in use


def get_status() -> Dict[str, Any]:
    """Get server status with automatic stale file cleanup.

    Returns:
        Dict with 'running' (bool), and if running: 'pid', 'host', 'port',
        'started_at', 'url'. May include 'was_stale' if a stale file was cleaned.
    """
    state = read_state_file()
    if state is None:
        return {"running": False, "pid": None}

    pid = state.get("pid")
    if pid is None:
        cleanup_state_files()
        return {"running": False, "pid": None}

    # Check 1: Process exists?
    if not is_process_running(pid):
        cleanup_state_files()
        return {"running": False, "pid": None, "was_stale": True}

    # Check 2: Is it actually our process?
    if not is_our_process(pid):
        cleanup_state_files()
        return {"running": False, "pid": None, "was_stale": True}

    # Process is running
    return {
        "running": True,
        "pid": pid,
        "host": state.get("host", "127.0.0.1"),
        "port": state.get("port", 5555),
        "started_at": state.get("started_at"),
        "url": f"http://{state.get('host', '127.0.0.1')}:{state.get('port', 5555)}",
    }


def start_background_server(host: str, port: int) -> Dict[str, Any]:
    """Start the Flask server as a background process.

    Args:
        host: Host to bind to
        port: Port to bind to

    Returns:
        Dict with 'success' (bool), and on success: 'pid', 'url', 'log_file'.
        On failure: 'message' with error description.
    """
    # Step 1: Validate current state (auto-cleans stale files)
    status = get_status()
    if status["running"]:
        return {
            "success": False,
            "message": f"Server already running (PID: {status['pid']})",
        }

    # Step 2: Check port availability
    if is_port_in_use(host, port):
        return {
            "success": False,
            "message": f"Port {port} is already in use",
        }

    # Build command to run the server
    cmd = [
        sys.executable,
        "-m",
        "waqt.wsgi_server",
        "--host",
        host,
        "--port",
        str(port),
    ]

    # Platform-specific daemonization
    kwargs: Dict[str, Any] = {}
    if sys.platform == "win32":
        # Windows: use DETACHED_PROCESS
        DETACHED_PROCESS = 0x00000008
        kwargs["creationflags"] = DETACHED_PROCESS
    else:
        # Unix: start new session
        kwargs["start_new_session"] = True

    # Redirect output to log file
    log_file = get_log_file_path()

    try:
        with open(log_file, "a") as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                **kwargs,
            )

        # Write state file
        state = {
            "pid": process.pid,
            "port": port,
            "host": host,
            "started_at": datetime.now().isoformat(),
        }
        write_state_file(state)

        return {
            "success": True,
            "pid": process.pid,
            "url": f"http://{host}:{port}",
            "log_file": str(log_file),
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to start server: {str(e)}",
        }


def stop_server(force: bool = False) -> Dict[str, Any]:
    """Stop the background server.

    Args:
        force: If True, use SIGKILL instead of SIGTERM (Unix) or /F flag (Windows)

    Returns:
        Dict with 'success' (bool), and on success: 'pid'.
        On failure: 'message' with error description.
    """
    status = get_status()
    if not status["running"]:
        return {"success": False, "message": "Server is not running"}

    pid = status["pid"]

    try:
        if sys.platform == "win32":
            # Windows: use taskkill
            args = ["taskkill", "/PID", str(pid)]
            if force:
                args.insert(1, "/F")
            subprocess.run(args, capture_output=True)
        else:
            # Unix: send signal
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)

        # Wait for process to terminate
        import time

        for _ in range(10):  # Wait up to 5 seconds
            if not is_process_running(pid):
                break
            time.sleep(0.5)

        cleanup_state_files()
        return {"success": True, "pid": pid}

    except Exception as e:
        return {"success": False, "message": str(e)}


def get_uptime(started_at: Optional[str]) -> Optional[str]:
    """Calculate uptime from started_at timestamp.

    Returns a human-readable string like "2h 15m" or None if invalid.
    """
    if not started_at:
        return None

    try:
        start = datetime.fromisoformat(started_at)
        delta = datetime.now() - start
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    except Exception:
        return None
