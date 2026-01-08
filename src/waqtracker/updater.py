"""Update checking and self-update functionality for waqtracker.

This module provides functionality to check for updates and self-update
the waqtracker executable when running as a frozen PyInstaller binary.
"""

import sys
import os
import platform
import urllib.request
import urllib.error
import json
import zipfile
import shutil
import tempfile
from typing import Optional, Tuple, Dict
from pathlib import Path

from ._version import VERSION, REPO_URL


def parse_version(version_str: str) -> Tuple[int, int, int, bool, str]:
    """Parse a version string into comparable components.

    Args:
        version_str: Version string like "0.1.0" or "0.1.93-dev"

    Returns:
        Tuple of (major, minor, patch, is_prerelease, prerelease_suffix)

    Examples:
        "0.1.0" -> (0, 1, 0, False, "")
        "0.1.93-dev" -> (0, 1, 93, True, "dev")
    """
    version_str = version_str.lstrip("v")  # Remove leading 'v' if present

    # Split on '-' to separate version from suffix
    parts = version_str.split("-", 1)
    version_part = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""

    # Parse version numbers
    version_nums = version_part.split(".")
    major = int(version_nums[0]) if len(version_nums) > 0 else 0
    minor = int(version_nums[1]) if len(version_nums) > 1 else 0
    patch = int(version_nums[2]) if len(version_nums) > 2 else 0

    is_prerelease = bool(suffix)

    return (major, minor, patch, is_prerelease, suffix)


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2

    Note:
        Prerelease versions (e.g., "0.1.93-dev") are considered less than
        release versions (e.g., "0.1.93").
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    # Compare major, minor, patch
    for i in range(3):
        if v1[i] < v2[i]:
            return -1
        elif v1[i] > v2[i]:
            return 1

    # If version numbers are equal, check prerelease status
    # Prerelease < Release
    if v1[3] and not v2[3]:  # v1 is prerelease, v2 is not
        return -1
    elif not v1[3] and v2[3]:  # v1 is not prerelease, v2 is
        return 1

    # Both are same type (both prerelease or both release)
    return 0


def is_frozen() -> bool:
    """Check if the application is running as a frozen executable (PyInstaller)."""
    return getattr(sys, "frozen", False)


def get_platform_info() -> Tuple[str, str]:
    """Detect the current platform and architecture.

    Returns:
        Tuple of (os_name, architecture) like ("linux", "amd64")
    """
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Map OS
    if system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "macos"
    elif system == "windows":
        os_name = "windows"
    else:
        os_name = system

    # Map architecture
    if machine in ("x86_64", "amd64", "x64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine

    return os_name, arch


def get_asset_name(os_name: str, arch: str) -> str:
    """Generate the expected asset name for a platform.

    Args:
        os_name: Operating system name (linux, macos, windows)
        arch: Architecture (amd64, arm64)

    Returns:
        Asset name like "waqtracker-linux-amd64.zip"
    """
    return f"waqtracker-{os_name}-{arch}.zip"


def check_for_updates(
    timeout: int = 10, prerelease: bool = False
) -> Optional[Dict[str, str]]:
    """Check GitHub Releases for newer versions.

    Args:
        timeout: Request timeout in seconds
        prerelease: If True, check the 'dev' tag; otherwise check 'latest'

    Returns:
        Dictionary with update info if update available, None otherwise.
        Dictionary contains: 'version', 'url', 'tag_name', 'is_prerelease'
    """
    # Extract owner/repo from REPO_URL
    # Example: "https://github.com/GMouaad/waqt" -> "GMouaad/waqt"
    repo_path = REPO_URL.rstrip("/").split("github.com/")[-1]

    # Construct API URL
    if prerelease:
        # Check specific 'dev' tag
        api_url = f"https://api.github.com/repos/{repo_path}/releases/tags/dev"
    else:
        # Check latest stable release
        api_url = f"https://api.github.com/repos/{repo_path}/releases/latest"

    try:
        # Fetch release information
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"waqtracker/{VERSION}",
            },
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        # Extract version information
        tag_name = data.get("tag_name", "")
        remote_version = tag_name.lstrip("v")

        # Compare versions
        if compare_versions(remote_version, VERSION) > 0:
            # Update available
            return {
                "version": remote_version,
                "tag_name": tag_name,
                "url": data.get("html_url", ""),
                "is_prerelease": data.get("prerelease", False),
                "assets": data.get("assets", []),
            }

        return None  # No update available

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Release not found (e.g., 'dev' tag doesn't exist yet)
            return None
        raise
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        # Network error or invalid response
        raise Exception(f"Failed to check for updates: {e}")


def download_and_install_update(
    release_info: Dict[str, str], confirm: bool = True
) -> bool:
    """Download and install an update.

    Args:
        release_info: Release information from check_for_updates()
        confirm: If True, prompt user for confirmation before proceeding

    Returns:
        True if update was successful, False otherwise

    Raises:
        Exception: If not running as frozen executable or download fails
    """
    if not is_frozen():
        raise Exception(
            "Self-update is only available for frozen executables. "
            "You are running from source. "
            "Please update using: git pull && uv pip install -e ."
        )

    # Get platform info
    os_name, arch = get_platform_info()
    expected_asset_name = get_asset_name(os_name, arch)

    # Find the asset for this platform
    asset_url = None
    for asset in release_info.get("assets", []):
        if asset.get("name") == expected_asset_name:
            asset_url = asset.get("browser_download_url")
            break

    if not asset_url:
        raise Exception(
            f"No asset found for platform {os_name}-{arch}. "
            f"Expected asset name: {expected_asset_name}"
        )

    # Get current executable path
    current_exe = sys.executable

    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / expected_asset_name
        extract_path = temp_path / "extracted"
        extract_path.mkdir()

        # Download the asset
        print(f"Downloading {expected_asset_name}...")
        try:
            urllib.request.urlretrieve(asset_url, zip_path)
        except Exception as e:
            raise Exception(f"Failed to download update: {e}")

        # Extract the zip
        print("Extracting...")
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
        except Exception as e:
            raise Exception(f"Failed to extract update: {e}")

        # Find the executable in the extracted files
        if os_name == "windows":
            new_exe_name = "waqtracker.exe"
        else:
            new_exe_name = "waqtracker"

        new_exe_path = extract_path / new_exe_name

        if not new_exe_path.exists():
            raise Exception(f"Executable not found in archive: {new_exe_name}")

        # Replace the current executable
        print("Installing update...")
        try:
            # Backup current executable
            backup_path = Path(current_exe).with_suffix(".bak")
            if backup_path.exists():
                backup_path.unlink()
            shutil.copy2(current_exe, backup_path)

            # Replace with new executable
            shutil.copy2(new_exe_path, current_exe)

            # Make executable on Unix
            if os_name != "windows":
                os.chmod(current_exe, 0o755)

            # Remove backup
            backup_path.unlink()

            print(f"✓ Successfully updated to version {release_info['version']}")
            return True

        except Exception as e:
            # Try to restore backup on error
            if backup_path.exists():
                try:
                    shutil.copy2(backup_path, current_exe)
                    backup_path.unlink()
                    print("Restored previous version after error")
                except Exception:
                    pass
            raise Exception(f"Failed to install update: {e}")
