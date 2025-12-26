from __future__ import annotations

import pytest
from hatchling.metadata.plugin.interface import MetadataHookInterface

from hatchling_autoextras_hook.hooks import (
    AutoExtrasMetadataHook,
    hatch_register_metadata_hook,
)


def test_plugin_name() -> None:
    """Test that the plugin name is correct."""
    assert AutoExtrasMetadataHook.PLUGIN_NAME == "autoextras"


def test_invalid_group_name() -> None:
    with pytest.raises(ValueError, match=r"'group-name' must be a non-empty string"):
        AutoExtrasMetadataHook("test", {"group-name": " "})


def test_invalid_exclude_type() -> None:
    with pytest.raises(TypeError, match=r"'exclude' must be a list of extra names"):
        AutoExtrasMetadataHook("test", {"exclude": "dev"})


def test_invalid_overwrite_type() -> None:
    with pytest.raises(TypeError, match=r"'overwrite' must be a boolean"):
        AutoExtrasMetadataHook("test", {"overwrite": "true"})


def test_update_default_group_name() -> None:
    """Test that the default group name is 'all'."""
    hook = AutoExtrasMetadataHook("test", {})
    metadata = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=4.0"],
        }
    }
    hook.update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": ["black>=22.0", "pytest>=7.0", "sphinx>=4.0"],
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=4.0"],
        }
    }


def test_update_custom_group_name() -> None:
    """Test that a custom group name can be configured."""
    hook = AutoExtrasMetadataHook("test", {"group-name": "complete"})
    metadata = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=4.0"],
        }
    }
    hook.update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "complete": ["black>=22.0", "pytest>=7.0", "sphinx>=4.0"],
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=4.0"],
        }
    }


def test_update_with_no_optional_dependencies() -> None:
    """Test that update does nothing when there are no optional
    dependencies."""
    metadata = {}
    AutoExtrasMetadataHook(root="test", config={}).update(metadata)
    assert metadata == {"optional-dependencies": {"all": []}}


def test_update_with_empty_optional_dependencies() -> None:
    """Test that update does nothing when optional dependencies is
    empty."""
    metadata = {"optional-dependencies": {}}
    AutoExtrasMetadataHook(root="test", config={}).update(metadata)
    assert metadata == {"optional-dependencies": {"all": []}}


def test_update_with_single_extra() -> None:
    """Test that update creates 'all' extra with dependencies from one
    extra."""
    metadata = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=22.0"],
        }
    }
    AutoExtrasMetadataHook(root="test", config={}).update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": ["black>=22.0", "pytest>=7.0"],
            "dev": ["pytest>=7.0", "black>=22.0"],
        }
    }


def test_update_with_multiple_extras() -> None:
    """Test that update creates 'all' extra combining all extras."""
    metadata = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=5.0", "sphinx-rtd-theme>=1.0"],
            "typing": ["mypy>=1.0"],
        }
    }
    AutoExtrasMetadataHook(root="test", config={}).update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": [
                "black>=22.0",
                "mypy>=1.0",
                "pytest>=7.0",
                "sphinx-rtd-theme>=1.0",
                "sphinx>=5.0",
            ],
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=5.0", "sphinx-rtd-theme>=1.0"],
            "typing": ["mypy>=1.0"],
        }
    }


def test_update_with_duplicate_dependencies() -> None:
    """Test that update handles duplicate dependencies across extras."""
    metadata = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=22.0"],
            "test": ["pytest>=7.0", "coverage>=6.0"],
        }
    }
    AutoExtrasMetadataHook(root="test", config={}).update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": ["black>=22.0", "coverage>=6.0", "pytest>=7.0"],
            "dev": ["pytest>=7.0", "black>=22.0"],
            "test": ["pytest>=7.0", "coverage>=6.0"],
        }
    }


def test_update_sorts_dependencies() -> None:
    """Test that dependencies in 'all' extra are sorted."""
    metadata = {
        "optional-dependencies": {
            "dev": ["zzz-package", "aaa-package", "mmm-package"],
        }
    }
    AutoExtrasMetadataHook(root="test", config={}).update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": ["aaa-package", "mmm-package", "zzz-package"],
            "dev": ["zzz-package", "aaa-package", "mmm-package"],
        }
    }


def test_update_does_not_overwrite_all() -> None:
    """Test that update raises an error if 'all' extra already
    exists."""
    metadata = {
        "optional-dependencies": {
            "all": ["old-dependency"],
            "dev": ["pytest>=7.0", "black>=22.0"],
        }
    }
    hook = AutoExtrasMetadataHook(root="test", config={})
    with pytest.raises(RuntimeError, match=r"Cannot create 'all' group: already exists."):
        hook.update(metadata)


def test_update_overwrite_all() -> None:
    """Test that update raises an error if 'all' extra already
    exists."""
    metadata = {
        "optional-dependencies": {
            "all": ["old-dependency"],
            "dev": ["pytest>=7.0", "black>=22.0"],
        }
    }
    AutoExtrasMetadataHook(root="test", config={"overwrite": True}).update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": ["black>=22.0", "pytest>=7.0"],
            "dev": ["pytest>=7.0", "black>=22.0"],
        }
    }


def test_update_with_exclude() -> None:
    """Test that update excludes some extras."""
    metadata = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=5.0", "sphinx-rtd-theme>=1.0"],
            "typing": ["mypy>=1.0"],
        }
    }
    AutoExtrasMetadataHook(root="test", config={"exclude": ["dev"]}).update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "all": ["mypy>=1.0", "sphinx-rtd-theme>=1.0", "sphinx>=5.0"],
            "dev": ["pytest>=7.0", "black>=22.0"],
            "docs": ["sphinx>=5.0", "sphinx-rtd-theme>=1.0"],
            "typing": ["mypy>=1.0"],
        }
    }


def test_hatch_register_metadata_hook_returns_correct_class() -> None:
    """Ensure the plugin registration function returns the correct hook
    class."""
    hook_class = hatch_register_metadata_hook()
    # The returned object must be a class
    assert isinstance(hook_class, type)
    assert hook_class is AutoExtrasMetadataHook
    assert issubclass(hook_class, MetadataHookInterface)
