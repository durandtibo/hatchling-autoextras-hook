from __future__ import annotations

import logging

import pytest
from hatchling.metadata.plugin.interface import MetadataHookInterface

from hatchling_autoextras_hook.hooks import (
    AutoExtrasMetadataHook,
    hatch_register_metadata_hook,
)


def test_plugin_name() -> None:
    """Test that the plugin name is correct."""
    assert AutoExtrasMetadataHook.PLUGIN_NAME == "autoextras"


@pytest.mark.parametrize("group_name", ["", " ", "\t\n", None, 1, ["all"]])
def test_invalid_group_name(group_name: object) -> None:
    with pytest.raises(ValueError, match=r"'group-name' must be a non-empty string"):
        AutoExtrasMetadataHook("test", {"group-name": group_name})


@pytest.mark.parametrize("exclude", ["dev", ("dev",), {"dev"}, None, 1])
def test_invalid_exclude_type(exclude: object) -> None:
    with pytest.raises(TypeError, match=r"'exclude' must be a list of extra names"):
        AutoExtrasMetadataHook("test", {"exclude": exclude})


@pytest.mark.parametrize("overwrite", ["true", 1, 0, None])
def test_invalid_overwrite_type(overwrite: object) -> None:
    with pytest.raises(TypeError, match=r"'overwrite' must be a boolean"):
        AutoExtrasMetadataHook("test", {"overwrite": overwrite})


def test_default_config() -> None:
    hook = AutoExtrasMetadataHook("test", {})
    assert hook.config == {"group-name": "all", "exclude": [], "overwrite": False}


def test_config_overrides_defaults() -> None:
    hook = AutoExtrasMetadataHook(
        "test", {"group-name": "full", "exclude": ["dev"], "overwrite": True}
    )
    assert hook.config == {"group-name": "full", "exclude": ["dev"], "overwrite": True}


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
    """Test that update replaces an existing 'all' extra when overwrite
    is True."""
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


def test_update_strips_whitespace() -> None:
    metadata = {"optional-dependencies": {"dev": ["  pytest>=7.0 ", "pytest>=7.0"]}}
    AutoExtrasMetadataHook("test", {}).update(metadata)
    assert metadata["optional-dependencies"]["all"] == ["pytest>=7.0"]


def test_update_ignores_non_string_dependencies() -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest", 1, None, "black"]}}
    AutoExtrasMetadataHook("test", {}).update(metadata)
    assert metadata["optional-dependencies"]["all"] == ["black", "pytest"]


def test_update_exclude_unknown_extra_is_ignored() -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest"]}}
    AutoExtrasMetadataHook("test", {"exclude": ["missing"]}).update(metadata)
    assert metadata["optional-dependencies"]["all"] == ["pytest"]


def test_update_exclude_all_extras() -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest"], "docs": ["sphinx"]}}
    AutoExtrasMetadataHook("test", {"exclude": ["dev", "docs"]}).update(metadata)
    assert metadata["optional-dependencies"]["all"] == []


def test_update_overwrite_with_exclude() -> None:
    metadata = {"optional-dependencies": {"all": ["old"], "dev": ["pytest"], "docs": ["sphinx"]}}
    AutoExtrasMetadataHook("test", {"overwrite": True, "exclude": ["dev"]}).update(metadata)
    assert metadata["optional-dependencies"]["all"] == ["sphinx"]


def test_update_does_not_overwrite_custom_group() -> None:
    metadata = {"optional-dependencies": {"complete": ["old"], "dev": ["pytest"]}}
    hook = AutoExtrasMetadataHook("test", {"group-name": "complete"})
    with pytest.raises(RuntimeError, match=r"Cannot create 'complete' group") as exc_info:
        hook.update(metadata)
    assert "overwrite = true" in str(exc_info.value)
    assert metadata["optional-dependencies"]["complete"] == ["old"]


def test_update_all_exists_when_custom_group_name() -> None:
    """An existing 'all' extra is treated as a regular extra when the
    group name differs."""
    metadata = {"optional-dependencies": {"all": ["numpy"], "dev": ["pytest"]}}
    AutoExtrasMetadataHook("test", {"group-name": "complete"}).update(metadata)
    assert metadata["optional-dependencies"]["complete"] == ["numpy", "pytest"]


def test_update_does_not_modify_source_extras() -> None:
    dev = ["pytest", "black"]
    metadata = {"optional-dependencies": {"dev": dev}}
    AutoExtrasMetadataHook("test", {}).update(metadata)
    assert dev == ["pytest", "black"]


def test_update_preserves_other_metadata() -> None:
    metadata = {"name": "pkg", "optional-dependencies": {"dev": ["pytest"]}}
    AutoExtrasMetadataHook("test", {}).update(metadata)
    assert metadata["name"] == "pkg"


def test_update_is_idempotent_with_overwrite() -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest"]}}
    hook = AutoExtrasMetadataHook("test", {"overwrite": True})
    hook.update(metadata)
    first = {k: list(v) for k, v in metadata["optional-dependencies"].items()}
    hook.update(metadata)
    assert metadata["optional-dependencies"] == first


def test_update_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest"]}}
    with caplog.at_level(logging.DEBUG, logger="hatchling_autoextras_hook.hooks"):
        AutoExtrasMetadataHook("test", {}).update(metadata)
    assert "Created 'all' with 1 dependencies from 1 extras" in caplog.text
