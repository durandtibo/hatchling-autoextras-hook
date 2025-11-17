"""Tests for the autoextras metadata hook."""

import pytest

from hatchling_autoextras_hook.hooks import AutoExtrasMetadataHook


class TestAutoExtrasMetadataHook:
    """Tests for AutoExtrasMetadataHook."""

    def test_plugin_name(self):
        """Test that the plugin name is correct."""
        assert AutoExtrasMetadataHook.PLUGIN_NAME == "autoextras"

    def test_update_with_no_optional_dependencies(self):
        """Test that update does nothing when there are no optional dependencies."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {}
        hook.update(metadata)
        assert metadata == {}

    def test_update_with_empty_optional_dependencies(self):
        """Test that update does nothing when optional dependencies is empty."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {"optional-dependencies": {}}
        hook.update(metadata)
        assert metadata == {"optional-dependencies": {}}

    def test_update_with_single_extra(self):
        """Test that update creates 'all' extra with dependencies from one extra."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {
            "optional-dependencies": {
                "dev": ["pytest>=7.0", "black>=22.0"],
            }
        }
        hook.update(metadata)
        assert "all" in metadata["optional-dependencies"]
        assert set(metadata["optional-dependencies"]["all"]) == {"pytest>=7.0", "black>=22.0"}

    def test_update_with_multiple_extras(self):
        """Test that update creates 'all' extra combining all extras."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {
            "optional-dependencies": {
                "dev": ["pytest>=7.0", "black>=22.0"],
                "docs": ["sphinx>=5.0", "sphinx-rtd-theme>=1.0"],
                "typing": ["mypy>=1.0"],
            }
        }
        hook.update(metadata)
        assert "all" in metadata["optional-dependencies"]
        expected = {
            "pytest>=7.0",
            "black>=22.0",
            "sphinx>=5.0",
            "sphinx-rtd-theme>=1.0",
            "mypy>=1.0",
        }
        assert set(metadata["optional-dependencies"]["all"]) == expected

    def test_update_with_duplicate_dependencies(self):
        """Test that update handles duplicate dependencies across extras."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {
            "optional-dependencies": {
                "dev": ["pytest>=7.0", "black>=22.0"],
                "test": ["pytest>=7.0", "coverage>=6.0"],
            }
        }
        hook.update(metadata)
        assert "all" in metadata["optional-dependencies"]
        # pytest should only appear once
        assert metadata["optional-dependencies"]["all"].count("pytest>=7.0") == 1
        expected = {"pytest>=7.0", "black>=22.0", "coverage>=6.0"}
        assert set(metadata["optional-dependencies"]["all"]) == expected

    def test_update_preserves_existing_all_extra(self):
        """Test that update replaces existing 'all' extra."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {
            "optional-dependencies": {
                "all": ["old-dependency"],
                "dev": ["pytest>=7.0", "black>=22.0"],
            }
        }
        hook.update(metadata)
        assert "all" in metadata["optional-dependencies"]
        # 'all' should be regenerated from 'dev', not include old-dependency
        assert "old-dependency" not in metadata["optional-dependencies"]["all"]
        assert set(metadata["optional-dependencies"]["all"]) == {"pytest>=7.0", "black>=22.0"}

    def test_update_sorts_dependencies(self):
        """Test that dependencies in 'all' extra are sorted."""
        hook = AutoExtrasMetadataHook("test", {})
        metadata = {
            "optional-dependencies": {
                "dev": ["zzz-package", "aaa-package", "mmm-package"],
            }
        }
        hook.update(metadata)
        all_deps = metadata["optional-dependencies"]["all"]
        assert all_deps == ["aaa-package", "mmm-package", "zzz-package"]
