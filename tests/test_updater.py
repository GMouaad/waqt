"""Unit tests for the updater module."""

import pytest
from src.waqtracker.updater import (
    parse_version,
    compare_versions,
    get_platform_info,
    get_asset_name,
)


class TestVersionParsing:
    """Tests for version string parsing."""

    def test_parse_simple_version(self):
        """Test parsing a simple version string."""
        result = parse_version("0.1.0")
        assert result == (0, 1, 0, False, "")

    def test_parse_version_with_dev_suffix(self):
        """Test parsing a version with -dev suffix."""
        result = parse_version("0.1.93-dev")
        assert result == (0, 1, 93, True, "dev")

    def test_parse_version_with_v_prefix(self):
        """Test parsing a version with v prefix."""
        result = parse_version("v1.2.3")
        assert result == (1, 2, 3, False, "")

    def test_parse_version_with_rc_suffix(self):
        """Test parsing a version with -rc suffix."""
        result = parse_version("2.0.0-rc1")
        assert result == (2, 0, 0, True, "rc1")

    def test_parse_version_major_only(self):
        """Test parsing a version with only major number."""
        result = parse_version("1")
        assert result == (1, 0, 0, False, "")

    def test_parse_version_major_minor_only(self):
        """Test parsing a version with major and minor only."""
        result = parse_version("1.5")
        assert result == (1, 5, 0, False, "")


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_compare_equal_versions(self):
        """Test comparing equal versions."""
        assert compare_versions("0.1.0", "0.1.0") == 0
        assert compare_versions("1.2.3", "1.2.3") == 0

    def test_compare_different_major(self):
        """Test comparing versions with different major numbers."""
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("2.0.0", "1.0.0") == 1

    def test_compare_different_minor(self):
        """Test comparing versions with different minor numbers."""
        assert compare_versions("0.1.0", "0.2.0") == -1
        assert compare_versions("0.2.0", "0.1.0") == 1

    def test_compare_different_patch(self):
        """Test comparing versions with different patch numbers."""
        assert compare_versions("0.1.1", "0.1.2") == -1
        assert compare_versions("0.1.2", "0.1.1") == 1

    def test_compare_prerelease_vs_release(self):
        """Test that prerelease versions are less than release versions."""
        assert compare_versions("0.1.93-dev", "0.1.93") == -1
        assert compare_versions("0.1.93", "0.1.93-dev") == 1

    def test_compare_two_prereleases(self):
        """Test comparing two prerelease versions."""
        assert compare_versions("0.1.92-dev", "0.1.93-dev") == -1
        assert compare_versions("0.1.93-dev", "0.1.92-dev") == 1

    def test_compare_with_v_prefix(self):
        """Test that v prefix is handled correctly."""
        assert compare_versions("v0.1.0", "0.1.1") == -1
        assert compare_versions("v1.0.0", "v1.0.0") == 0

    def test_compare_complex_scenario(self):
        """Test a complex version comparison scenario."""
        # 0.1.92-dev < 0.1.93-dev < 0.1.93 < 0.1.94
        assert compare_versions("0.1.92-dev", "0.1.93-dev") == -1
        assert compare_versions("0.1.93-dev", "0.1.93") == -1
        assert compare_versions("0.1.93", "0.1.94") == -1

    def test_compare_different_prerelease_suffixes(self):
        """Test that different prerelease suffixes are compared lexicographically."""
        # alpha < beta < dev < rc (lexicographically)
        assert compare_versions("0.1.93-alpha", "0.1.93-beta") == -1
        assert compare_versions("0.1.93-beta", "0.1.93-dev") == -1
        assert compare_versions("0.1.93-dev", "0.1.93-rc") == -1
        assert compare_versions("0.1.93-rc", "0.1.93-alpha") == 1


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_get_platform_info(self):
        """Test that platform info is returned in expected format."""
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
        assert get_asset_name("linux", "amd64") == "waqtracker-linux-amd64.zip"
        assert get_asset_name("macos", "arm64") == "waqtracker-macos-arm64.zip"
        assert get_asset_name("windows", "amd64") == "waqtracker-windows-amd64.zip"


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
        from src.waqtracker.updater import check_for_updates

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
