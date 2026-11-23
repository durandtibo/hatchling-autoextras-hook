from __future__ import annotations

import logging

import pytest
from hatchling.metadata.plugin.interface import MetadataHookInterface

from hatchling_autoextras_hook.hooks import (
    AutoExtrasMetadataHook,
    _normalize,
    _read_warn_only,
    hatch_register_metadata_hook,
)

WARN_ONLY_ENV = "HATCHLING_AUTOEXTRAS_WARN_ONLY"


@pytest.fixture(autouse=True)
def _unset_warn_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the tests independent of the environment of the caller."""
    monkeypatch.delenv(WARN_ONLY_ENV, raising=False)


def test_plugin_name() -> None:
    """Test that the plugin name is correct."""
    assert AutoExtrasMetadataHook.PLUGIN_NAME == "autoextras"


@pytest.mark.parametrize("group_name", [None, 1, ["all"]])
def test_invalid_group_name_type(group_name: object) -> None:
    with pytest.raises(TypeError, match=r"'group-name' must be a string"):
        AutoExtrasMetadataHook("test", {"group-name": group_name})


@pytest.mark.parametrize(
    "group_name",
    ["", " ", "\t\n", " all ", "a b", "-a", "a-", "_a", "a_", ".a", "a.", "é", "all\n"],
)
def test_invalid_group_name_value(group_name: str) -> None:
    with pytest.raises(ValueError, match=r"'group-name' must be a valid extra name"):
        AutoExtrasMetadataHook("test", {"group-name": group_name})


@pytest.mark.parametrize(
    "group_name", ["all", "full", "my_extra", "my-extra", "a.b", "a", "A1", "9"]
)
def test_valid_group_name(group_name: str) -> None:
    hook = AutoExtrasMetadataHook("test", {"group-name": group_name})
    assert hook.config["group-name"] == group_name


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


@pytest.mark.parametrize("exclude", [[1], ["dev", None]])
def test_invalid_exclude_item_type(exclude: object) -> None:
    with pytest.raises(TypeError, match=r"'exclude' must be a list of extra names"):
        AutoExtrasMetadataHook("test", {"exclude": exclude})


@pytest.mark.parametrize("deps", ["pytest", ("pytest",), None, 1])
def test_update_invalid_extra_dependencies(deps: object) -> None:
    metadata = {"optional-dependencies": {"dev": deps}}
    with pytest.raises(TypeError, match=r"Dependencies of extra 'dev' must be a list"):
        AutoExtrasMetadataHook("test", {}).update(metadata)


@pytest.mark.parametrize("optional", [["pytest"], "pytest", 1])
def test_update_invalid_optional_dependencies(optional: object) -> None:
    with pytest.raises(TypeError, match=r"'optional-dependencies' must be a table"):
        AutoExtrasMetadataHook("test", {}).update({"optional-dependencies": optional})


def test_update_drops_blank_dependencies() -> None:
    metadata = {"optional-dependencies": {"dev": ["", "  ", "pytest"]}}
    AutoExtrasMetadataHook("test", {}).update(metadata)
    assert metadata["optional-dependencies"]["all"] == ["pytest"]


def test_update_failure_leaves_metadata_unchanged() -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest"], "docs": "sphinx"}}
    with pytest.raises(TypeError):
        AutoExtrasMetadataHook("test", {}).update(metadata)
    assert metadata == {"optional-dependencies": {"dev": ["pytest"], "docs": "sphinx"}}


def test_update_logs_overwrite(caplog: pytest.LogCaptureFixture) -> None:
    metadata = {"optional-dependencies": {"all": ["old"], "dev": ["pytest"]}}
    with caplog.at_level(logging.DEBUG, logger="hatchling_autoextras_hook.hooks"):
        AutoExtrasMetadataHook("test", {"overwrite": True}).update(metadata)
    assert "Overwriting existing 'all' group" in caplog.text


#########################################
#     Tests for the unknown options     #
#########################################


def test_unknown_option_raises() -> None:
    with pytest.raises(ValueError, match=r"Unknown option\(s\): \['excludes'\]"):
        AutoExtrasMetadataHook("test", {"excludes": ["dev"]})


def test_unknown_option_message_lists_valid_options() -> None:
    with pytest.raises(
        ValueError, match=r"Valid options: \['exclude', 'group-name', 'overwrite'\]"
    ):
        AutoExtrasMetadataHook("test", {"excludes": ["dev"]})


def test_unknown_options_are_reported_sorted() -> None:
    with pytest.raises(ValueError, match=r"Unknown option\(s\): \['alpha', 'zeta'\]"):
        AutoExtrasMetadataHook("test", {"zeta": 1, "alpha": 2})


def test_unknown_option_with_valid_options_raises() -> None:
    with pytest.raises(ValueError, match=r"Unknown option\(s\): \['typo'\]"):
        AutoExtrasMetadataHook("test", {"group-name": "full", "typo": True})


def test_unknown_option_warn_only_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    with pytest.warns(UserWarning, match=r"Unknown option\(s\): \['excludes'\]"):
        AutoExtrasMetadataHook("test", {"excludes": ["dev"]})


def test_unknown_option_warn_only_is_dropped_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    with pytest.warns(UserWarning, match=r"Unknown option"):
        hook = AutoExtrasMetadataHook("test", {"excludes": ["dev"], "group-name": "full"})
    assert hook.config == {"group-name": "full", "exclude": [], "overwrite": False}


def test_unknown_option_warn_only_ignores_the_option(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    metadata = {"optional-dependencies": {"dev": ["pytest"], "docs": ["sphinx"]}}
    with pytest.warns(UserWarning, match=r"Unknown option"):
        hook = AutoExtrasMetadataHook("test", {"excludes": ["dev"]})
    hook.update(metadata)
    assert metadata == {
        "optional-dependencies": {
            "dev": ["pytest"],
            "docs": ["sphinx"],
            "all": ["pytest", "sphinx"],
        }
    }


def test_warn_only_does_not_downgrade_invalid_group_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    with pytest.raises(ValueError, match=r"'group-name' must be a valid extra name"):
        AutoExtrasMetadataHook("test", {"group-name": ""})


def test_warn_only_does_not_downgrade_invalid_exclude(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    with pytest.raises(TypeError, match=r"'exclude' must be a list of extra names"):
        AutoExtrasMetadataHook("test", {"exclude": "dev"})


def test_warn_only_does_not_downgrade_invalid_overwrite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    with pytest.raises(TypeError, match=r"'overwrite' must be a boolean"):
        AutoExtrasMetadataHook("test", {"overwrite": "true"})


def test_default_config_is_not_shared_between_hooks() -> None:
    hook1 = AutoExtrasMetadataHook("test", {})
    hook1.config["exclude"].append("dev")
    assert AutoExtrasMetadataHook("test", {}).config["exclude"] == []


###############################
#     Tests for _report       #
###############################


def test_report_raises_by_default() -> None:
    hook = AutoExtrasMetadataHook("test", {})
    with pytest.raises(ValueError, match=r"something is wrong"):
        hook._report("something is wrong")


def test_report_warns_in_warn_only_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "1")
    hook = AutoExtrasMetadataHook("test", {})
    with pytest.warns(UserWarning, match=r"something is wrong"):
        hook._report("something is wrong")


#####################################
#     Tests for _read_warn_only     #
#####################################


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "True", "yes", "YES", "on", "On", " 1 "])
def test_read_warn_only_enabled(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, value)
    assert _read_warn_only() is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "NO", "off", "Off", "", "  "])
def test_read_warn_only_disabled(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, value)
    assert _read_warn_only() is False


def test_read_warn_only_unset() -> None:
    assert _read_warn_only() is False


@pytest.mark.parametrize("value", ["maybe", "2", "enabled", "y"])
def test_read_warn_only_invalid(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, value)
    with pytest.raises(ValueError, match=r"HATCHLING_AUTOEXTRAS_WARN_ONLY"):
        _read_warn_only()


def test_init_invalid_warn_only_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(WARN_ONLY_ENV, "maybe")
    with pytest.raises(ValueError, match=r"Invalid value 'maybe'"):
        AutoExtrasMetadataHook("test", {})


##############################
#     Tests for _normalize   #
##############################


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Dev_Extra", "dev-extra"),
        ("dev.extra", "dev-extra"),
        ("a..b", "a-b"),
        ("A-_-B", "a-b"),
        ("dev", "dev"),
        ("dev-extra", "dev-extra"),
        ("", ""),
    ],
)
def test_normalize(name: str, expected: str) -> None:
    assert _normalize(name) == expected


def test_normalize_is_idempotent() -> None:
    assert _normalize(_normalize("A_.b")) == "a-b"


#######################################
#     Tests for the normalized names  #
#######################################


@pytest.mark.parametrize("exclude", [["ALL"], ["All"], ["all"]])
def test_exclude_generated_extra_raises(exclude: list[str]) -> None:
    with pytest.raises(ValueError, match=r"'exclude' must not contain the generated extra 'all'"):
        AutoExtrasMetadataHook("test", {"exclude": exclude})


def test_exclude_generated_extra_other_spelling_raises() -> None:
    with pytest.raises(ValueError, match=r"'exclude' must not contain the generated extra"):
        AutoExtrasMetadataHook("test", {"group-name": "my_extra", "exclude": ["My.Extra"]})


def test_update_exclude_is_case_insensitive() -> None:
    metadata = {"optional-dependencies": {"a": ["x"], "b": ["y"]}}
    AutoExtrasMetadataHook("test", {"exclude": ["A"]}).update(metadata)
    assert metadata == {"optional-dependencies": {"a": ["x"], "b": ["y"], "all": ["y"]}}


def test_update_exclude_matches_other_separator() -> None:
    metadata = {"optional-dependencies": {"B_c": ["x"], "d": ["y"]}}
    AutoExtrasMetadataHook("test", {"exclude": ["B.c"]}).update(metadata)
    assert metadata == {"optional-dependencies": {"B_c": ["x"], "d": ["y"], "all": ["y"]}}


def test_update_conflict_is_case_insensitive() -> None:
    metadata = {"optional-dependencies": {"All": ["old"], "dev": ["pytest"]}}
    with pytest.raises(RuntimeError, match=r"Cannot create 'all' group: already exists"):
        AutoExtrasMetadataHook("test", {}).update(metadata)


def test_update_conflict_failure_leaves_metadata_unchanged() -> None:
    metadata = {"optional-dependencies": {"All": ["old"], "dev": ["pytest"]}}
    with pytest.raises(RuntimeError, match=r"already exists"):
        AutoExtrasMetadataHook("test", {}).update(metadata)
    assert metadata == {"optional-dependencies": {"All": ["old"], "dev": ["pytest"]}}


def test_update_conflict_with_other_separator() -> None:
    metadata = {"optional-dependencies": {"my.extra": ["old"], "dev": ["pytest"]}}
    with pytest.raises(RuntimeError, match=r"Cannot create 'my_extra' group: already exists"):
        AutoExtrasMetadataHook("test", {"group-name": "my_extra"}).update(metadata)


def test_update_overwrite_replaces_existing_spelling() -> None:
    metadata = {"optional-dependencies": {"All": ["old"], "dev": ["pytest"]}}
    AutoExtrasMetadataHook("test", {"overwrite": True}).update(metadata)
    assert metadata == {"optional-dependencies": {"dev": ["pytest"], "all": ["pytest"]}}


def test_update_overwrite_same_spelling_keeps_position() -> None:
    metadata = {"optional-dependencies": {"all": ["old"], "dev": ["pytest"]}}
    AutoExtrasMetadataHook("test", {"overwrite": True}).update(metadata)
    assert list(metadata["optional-dependencies"]) == ["all", "dev"]


def test_update_overwrite_logs_existing_spelling(caplog: pytest.LogCaptureFixture) -> None:
    metadata = {"optional-dependencies": {"ALL": ["old"], "dev": ["pytest"]}}
    with caplog.at_level(logging.DEBUG, logger="hatchling_autoextras_hook.hooks"):
        AutoExtrasMetadataHook("test", {"overwrite": True}).update(metadata)
    assert "Overwriting existing 'ALL' group" in caplog.text


def test_update_custom_group_name_with_exclude() -> None:
    metadata = {"optional-dependencies": {"dev": ["pytest"], "docs": ["sphinx"], "aws": ["boto3"]}}
    AutoExtrasMetadataHook("test", {"group-name": "full", "exclude": ["DEV", "docs"]}).update(
        metadata
    )
    assert metadata == {
        "optional-dependencies": {
            "dev": ["pytest"],
            "docs": ["sphinx"],
            "aws": ["boto3"],
            "full": ["boto3"],
        }
    }
