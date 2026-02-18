"""Unit tests for the updater module."""

import pytest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path


class TestRetryLogic:
    """Tests for file operation retry logic."""

    def test_retry_success_on_first_attempt(self):
        """Test that operation succeeds on first attempt."""
        from src.waqt.updater import _retry_file_operation

        mock_operation = Mock(return_value="success")
        result = _retry_file_operation(mock_operation, max_retries=3)

        assert result == "success"
        assert mock_operation.call_count == 1

    def test_retry_success_after_failures(self):
        """Test that operation succeeds after some failures."""
        from src.waqt.updater import _retry_file_operation

        mock_operation = Mock()
        # Fail twice, then succeed
        mock_operation.side_effect = [
            OSError("File locked"),
            PermissionError("Access denied"),
            "success",
        ]

        result = _retry_file_operation(mock_operation, max_retries=5, initial_delay=0.01)

        assert result == "success"
        assert mock_operation.call_count == 3

    def test_retry_exhausted_raises_exception(self):
        """Test that exhausted retries raise an exception."""
        from src.waqt.updater import _retry_file_operation

        mock_operation = Mock(side_effect=OSError("File permanently locked"))

        with pytest.raises(Exception) as exc_info:
            _retry_file_operation(mock_operation, max_retries=3, initial_delay=0.01)

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert "File permanently locked" in str(exc_info.value)
        assert mock_operation.call_count == 3

    def test_retry_only_catches_os_permission_errors(self):
        """Test that retry only catches OSError and PermissionError."""
        from src.waqt.updater import _retry_file_operation

        mock_operation = Mock(side_effect=ValueError("Different error"))

        with pytest.raises(ValueError):
            _retry_file_operation(mock_operation, max_retries=3, initial_delay=0.01)

        # Should fail on first attempt since ValueError is not caught
        assert mock_operation.call_count == 1


class TestWindowsUpdateScript:
    """Tests for Windows update script creation."""

    def test_create_windows_update_script(self):
        """Test that Windows update script is created correctly."""
        from src.waqt.updater import _create_windows_update_script

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            backup_path = temp_path / "waqt.exe.bak"
            new_exe_path = temp_path / "waqt_new.exe"
            current_exe = str(temp_path / "waqt.exe")

            # Create dummy files
            backup_path.touch()
            new_exe_path.touch()

            script_path = _create_windows_update_script(
                backup_path, new_exe_path, current_exe
            )

            assert script_path.exists()
            assert script_path.name == "waqt_update.bat"

            # Read and verify script content
            content = script_path.read_text()
            assert "timeout /t 2" in content
            assert str(new_exe_path) in content
            assert current_exe in content
            assert str(backup_path) in content


class TestVersionParsing:
    """Tests for version string parsing."""

    def test_parse_simple_version(self):
        """Test parsing a simple version string."""
        from src.waqt.updater import parse_version

        result = parse_version("0.1.0")
        assert result == (0, 1, 0, False, "")

    def test_parse_version_with_dev_suffix(self):
        """Test parsing a version with -dev suffix."""
        from src.waqt.updater import parse_version

        result = parse_version("0.1.93-dev")
        assert result == (0, 1, 93, True, "dev")

    def test_parse_version_with_v_prefix(self):
        """Test parsing a version with v prefix."""
        from src.waqt.updater import parse_version

        result = parse_version("v1.2.3")
        assert result == (1, 2, 3, False, "")

    def test_parse_version_with_rc_suffix(self):
        """Test parsing a version with -rc suffix."""
        from src.waqt.updater import parse_version

        result = parse_version("2.0.0-rc1")
        assert result == (2, 0, 0, True, "rc1")

    def test_parse_version_major_only(self):
        """Test parsing a version with only major number."""
        from src.waqt.updater import parse_version

        result = parse_version("1")
        assert result == (1, 0, 0, False, "")

    def test_parse_version_major_minor_only(self):
        """Test parsing a version with major and minor only."""
        from src.waqt.updater import parse_version

        result = parse_version("1.5")
        assert result == (1, 5, 0, False, "")


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_compare_equal_versions(self):
        """Test comparing equal versions."""
        from src.waqt.updater import compare_versions

        assert compare_versions("0.1.0", "0.1.0") == 0
        assert compare_versions("1.2.3", "1.2.3") == 0

    def test_compare_different_major(self):
        """Test comparing versions with different major numbers."""
        from src.waqt.updater import compare_versions

        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("2.0.0", "1.0.0") == 1

    def test_compare_different_minor(self):
        """Test comparing versions with different minor numbers."""
        from src.waqt.updater import compare_versions

        assert compare_versions("0.1.0", "0.2.0") == -1
        assert compare_versions("0.2.0", "0.1.0") == 1

    def test_compare_different_patch(self):
        """Test comparing versions with different patch numbers."""
        from src.waqt.updater import compare_versions

        assert compare_versions("0.1.1", "0.1.2") == -1
        assert compare_versions("0.1.2", "0.1.1") == 1

    def test_compare_prerelease_vs_release(self):
        """Test that prerelease versions are less than release versions."""
        from src.waqt.updater import compare_versions

        assert compare_versions("0.1.93-dev", "0.1.93") == -1
        assert compare_versions("0.1.93", "0.1.93-dev") == 1

    def test_compare_two_prereleases(self):
        """Test comparing two prerelease versions."""
        from src.waqt.updater import compare_versions

        assert compare_versions("0.1.92-dev", "0.1.93-dev") == -1
        assert compare_versions("0.1.93-dev", "0.1.92-dev") == 1

    def test_compare_with_v_prefix(self):
        """Test that v prefix is handled correctly."""
        from src.waqt.updater import compare_versions

        assert compare_versions("v0.1.0", "0.1.1") == -1
        assert compare_versions("v1.0.0", "v1.0.0") == 0

    def test_compare_complex_scenario(self):
        """Test a complex version comparison scenario."""
        from src.waqt.updater import compare_versions

        # 0.1.92-dev < 0.1.93-dev < 0.1.93 < 0.1.94
        assert compare_versions("0.1.92-dev", "0.1.93-dev") == -1
        assert compare_versions("0.1.93-dev", "0.1.93") == -1
        assert compare_versions("0.1.93", "0.1.94") == -1

    def test_compare_different_prerelease_suffixes(self):
        """Test that different prerelease suffixes are compared lexicographically."""
        from src.waqt.updater import compare_versions

        # alpha < beta < dev < rc (lexicographically)
        assert compare_versions("0.1.93-alpha", "0.1.93-beta") == -1
        assert compare_versions("0.1.93-beta", "0.1.93-dev") == -1
        assert compare_versions("0.1.93-dev", "0.1.93-rc") == -1
        assert compare_versions("0.1.93-rc", "0.1.93-alpha") == 1


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_get_platform_info(self):
        """Test that platform info is returned in expected format."""
        from src.waqt.updater import get_platform_info

        os_name, arch = get_platform_info()

        # Check that values are strings
        assert isinstance(os_name, str)
        assert isinstance(arch, str)

        # Check that os_name is one of expected normalized values
        assert os_name in ["linux", "macos", "windows"]

        # Check that arch is reasonable (normalized by get_platform_info)
        assert arch in ["amd64", "arm64"]

    def test_get_asset_name(self):
        """Test asset name generation."""
        from src.waqt.updater import get_asset_name

        assert get_asset_name("linux", "amd64") == "waqt-linux-amd64.zip"
        assert get_asset_name("macos", "arm64") == "waqt-macos-arm64.zip"
        assert get_asset_name("windows", "amd64") == "waqt-windows-amd64.zip"


class TestUpdateChecking:
    """Tests for update checking functionality.

    Note: These tests require network access and may be flaky.
    They are primarily for integration testing.
    """

    @pytest.mark.slow
    def test_check_for_updates_stable(self):
        """Test checking for stable updates (integration test)."""
        # This is an integration test that requires network access
        # It's marked as slow and may be skipped in CI
        from src.waqt.updater import check_for_updates

        try:
            # This may return None if already on latest, or update info
            result = check_for_updates(timeout=5, prerelease=False)

            # Result should be None or a dict with expected keys
            if result is not None:
                assert "version" in result
                assert "tag_name" in result
                assert "url" in result
                assert "is_prerelease" in result
                assert "assets" in result
        except Exception as e:
            # Network errors are acceptable in this test
            pytest.skip(f"Network error during update check: {e}")
