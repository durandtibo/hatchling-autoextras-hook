r"""Hatchling metadata hook to automatically generate 'all' extras."""

from __future__ import annotations

__all__ = ["AutoExtrasMetadataHook"]

import copy
import logging
import os
import re
import warnings
from typing import Any

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin import hookimpl

logger: logging.Logger = logging.getLogger(__name__)

# The options of the hook and their default values. This table is the single
# source of truth for the allowed keys of the hook table.
_DEFAULTS: dict[str, Any] = {"group-name": "all", "exclude": [], "overwrite": False}

# Valid name of an extra: the rule of hatchling (`is_valid_project_name`). It is
# copied because `hatchling.metadata.utils` is not public API.
_NAME_PATTERN = re.compile(r"^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$")

# Environment variable that downgrades the recoverable problems to warnings.
_WARN_ONLY_ENV = "HATCHLING_AUTOEXTRAS_WARN_ONLY"
_WARN_ONLY_TRUE = frozenset({"1", "true", "yes", "on"})
_WARN_ONLY_FALSE = frozenset({"0", "false", "no", "off", ""})


class AutoExtrasMetadataHook(MetadataHookInterface):
    r"""Metadata hook that automatically generates an 'all' extra.

    This hook collects all optional dependencies defined in the project
    and creates an 'all' extra that includes all of them.

    Configuration options (in pyproject.toml):
        group-name: Name of the combined extras group (default: "all")
        exclude: List of extra names to exclude from the combined group (default: [])
        overwrite: Whether to overwrite existing group (default: False)

    Extra names are compared after the normalization of PEP 685, like
    hatchling does: ``Dev_Extra``, ``dev-extra`` and ``dev.extra`` are
    the same extra. This applies to ``group-name``, ``exclude`` and to
    the check of an existing extra with the generated name.

    Unknown options are rejected with a ``ValueError``. Setting the
    environment variable ``HATCHLING_AUTOEXTRAS_WARN_ONLY`` to ``1``,
    ``true``, ``yes`` or ``on`` downgrades the recoverable problems
    (currently the unknown options) to a ``UserWarning``. ``0``,
    ``false``, ``no``, ``off``, an empty value or an unset variable
    keep the strict mode. Any other value raises a ``ValueError``.

    Example configuration:
        [tool.hatch.metadata.hooks.autoextras]
        group-name = "complete"
        exclude = ["dev", "test"]
        overwrite = false

    Example usage:

    ```pycon

    >>> from hatchling_autoextras_hook.hooks import AutoExtrasMetadataHook
    >>> metadata = {
    ...     "optional-dependencies": {
    ...         "dev": ["pytest>=7.0", "black>=22.0"],
    ...     }
    ... }
    >>> hook = AutoExtrasMetadataHook("test", {})
    >>> hook.update(metadata)
    >>> metadata
    {'optional-dependencies': {'dev': ['pytest>=7.0', 'black>=22.0'],
     'all': ['black>=22.0', 'pytest>=7.0']}}

    ```
    """

    PLUGIN_NAME: str = "autoextras"

    def __init__(self, root: str, config: dict[str, Any]) -> None:
        """Initialize the hook and validate configuration.

        Args:
            root: The root directory of the project.
            config: The plugin configuration dictionary.

        Raises:
            ValueError: If the configuration is invalid, or if the
                environment variable ``HATCHLING_AUTOEXTRAS_WARN_ONLY``
                has an unrecognized value.
            TypeError: If the configuration is invalid.
        """
        self._warn_only: bool = _read_warn_only()
        unknown = sorted(config.keys() - _DEFAULTS.keys())
        if unknown:
            self._report(f"Unknown option(s): {unknown}. Valid options: {sorted(_DEFAULTS)}")
        known = {key: value for key, value in config.items() if key in _DEFAULTS}
        super().__init__(root, copy.deepcopy(_DEFAULTS) | known)
        self._validate_config()

    def _report(self, msg: str) -> None:
        """Report a recoverable problem.

        The problem raises a ``ValueError`` by default. In warn-only
        mode, it emits a ``UserWarning`` and the build continues.

        Args:
            msg: The message that describes the problem.

        Raises:
            ValueError: If the warn-only mode is not enabled.
        """
        if not self._warn_only:
            raise ValueError(msg)
        warnings.warn(msg, UserWarning, stacklevel=2)

    def _validate_config(self) -> None:
        """Validate the plugin configuration.

        Raises:
            ValueError: If any configuration option is invalid, or if
                ``exclude`` contains the generated extra.
            TypeError: If any configuration option has a wrong type.
        """
        group_name = self.config["group-name"]
        if not isinstance(group_name, str):
            msg = "'group-name' must be a string"
            raise TypeError(msg)
        if not _NAME_PATTERN.fullmatch(group_name):
            msg = (
                f"'group-name' must be a valid extra name (letters, digits, '-', '_' and '.', "
                f"starting and ending with a letter or a digit), got {group_name!r}"
            )
            raise ValueError(msg)

        exclude = self.config["exclude"]
        if not isinstance(exclude, list) or not all(isinstance(name, str) for name in exclude):
            msg = "'exclude' must be a list of extra names"
            raise TypeError(msg)

        overwrite = self.config["overwrite"]
        if not isinstance(overwrite, bool):
            msg = "'overwrite' must be a boolean"
            raise TypeError(msg)

        # The normalized values are computed once, so `update` does no conversion
        self._group: str = _normalize(group_name)
        self._exclude: frozenset[str] = frozenset(_normalize(name) for name in exclude)
        if self._group in self._exclude:
            msg = f"'exclude' must not contain the generated extra '{group_name}'"
            raise ValueError(msg)

    def update(self, metadata: dict[str, Any]) -> None:
        r"""Update the project metadata to add the configured extras
        group.

        This method collects all dependencies from all optional extras
        (excluding any existing group with the configured name and any
        extras in the exclude list), removes duplicate strings, sorts
        them alphabetically, and creates/updates the extras group with
        the combined list. Two dependencies are duplicates if they are
        the same string after stripping the whitespace around them:
        the requirements are not parsed, hatchling merges the
        equivalent ones afterwards.

        Everything is validated before ``metadata`` is modified, so
        ``metadata`` is unchanged if this method raises.

        Args:
            metadata: The project metadata dictionary to update. This
                dictionary is modified in place.

        Raises:
            RuntimeError: If the configured group name already exists and
                overwrite is False.
            ValueError: If ``exclude`` contains a name that matches no
                extra (a warning in the warn-only mode), or if a
                dependency is a blank string.
            TypeError: If optional dependencies are not in the expected
                format: the table of extras, the dependencies of an
                extra and each dependency must be a table, a list and a
                string respectively.

        Note:
            If no optional dependencies exist, an empty group is
            created. Any pre-existing extras group will be completely
            replaced if overwrite is True. The dependencies of an
            excluded extra are not inspected.
        """
        optional_dependencies = metadata.get("optional-dependencies", {})
        if not isinstance(optional_dependencies, dict):
            msg = "'optional-dependencies' must be a table of extras"
            raise TypeError(msg)

        group_name = self.config["group-name"]
        by_name = {_normalize(name): name for name in optional_dependencies}
        existing = by_name.get(self._group)
        if existing is not None and not self.config["overwrite"]:
            msg = (
                f"Cannot create '{group_name}' group: already exists. "
                f"Existing extras: {list(optional_dependencies)}. "
                f"Configure a different 'group-name' in pyproject.toml or set 'overwrite = true'"
            )
            raise RuntimeError(msg)
        unmatched = sorted(self._exclude - by_name.keys())
        if unmatched:
            self._report(f"'exclude' contains names that match no extra: {unmatched}")

        # Collect the dependencies of the extras that are not excluded
        sources = [
            name
            for name in optional_dependencies
            if (key := _normalize(name)) != self._group and key not in self._exclude
        ]
        dependencies = {
            dep for name in sources for dep in _dependencies(name, optional_dependencies[name])
        }

        # Everything is valid: the metadata is modified in one last step
        if existing is not None:
            logger.debug("Overwriting existing '%s' group", existing)
            if existing != group_name:
                del optional_dependencies[existing]
        optional_dependencies[group_name] = sorted(dependencies)
        # The key is absent from the metadata only if `optional_dependencies` is a new dict
        metadata["optional-dependencies"] = optional_dependencies

        logger.debug(
            "Created '%s' with %d dependencies from %d extras: %s",
            group_name,
            len(dependencies),
            len(sources),
            sources,
        )


def _dependencies(name: str, value: object) -> list[str]:
    r"""Validate the dependencies of an extra and strip them.

    Args:
        name: The name of the extra, used in the error messages.
        value: The value of the extra in the metadata.

    Returns:
        The dependencies, stripped, in their original order.

    Raises:
        TypeError: If ``value`` is not a list, or if one of its items
            is not a string.
        ValueError: If one of the items is blank.

    Example usage:

    ```pycon

    >>> from hatchling_autoextras_hook.hooks import _dependencies
    >>> _dependencies("dev", [" pytest>=7.0 ", "black"])
    ['pytest>=7.0', 'black']

    ```
    """
    if not isinstance(value, list):
        msg = f"Dependencies of extra '{name}' must be a list of strings"
        raise TypeError(msg)
    dependencies = []
    for position, dep in enumerate(value, start=1):
        if not isinstance(dep, str):
            msg = f"Dependency #{position} of extra '{name}' must be a string, got {dep!r}"
            raise TypeError(msg)
        if not (stripped := dep.strip()):
            msg = f"Dependency #{position} of extra '{name}' must not be blank"
            raise ValueError(msg)
        dependencies.append(stripped)
    return dependencies


def _normalize(name: str) -> str:
    r"""Normalize the name of an extra (PEP 685 and PEP 503).

    Args:
        name: The name of the extra.

    Returns:
        The normalized name: lowercase, with every run of ``-``, ``_``
            and ``.`` replaced by one ``-``.

    Example usage:

    ```pycon

    >>> from hatchling_autoextras_hook.hooks import _normalize
    >>> _normalize("Dev_Extra")
    'dev-extra'

    ```
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def _read_warn_only() -> bool:
    r"""Read the warn-only mode from the environment.

    Returns:
        ``True`` if ``HATCHLING_AUTOEXTRAS_WARN_ONLY`` is set to ``1``,
            ``true``, ``yes`` or ``on`` (case-insensitive), ``False`` if
            it is unset, empty or set to ``0``, ``false``, ``no`` or
            ``off``.

    Raises:
        ValueError: If the variable has any other value.

    Example usage:

    ```pycon

    >>> import os
    >>> from hatchling_autoextras_hook.hooks import _read_warn_only
    >>> os.environ["HATCHLING_AUTOEXTRAS_WARN_ONLY"] = "On"
    >>> _read_warn_only()
    True
    >>> del os.environ["HATCHLING_AUTOEXTRAS_WARN_ONLY"]
    >>> _read_warn_only()
    False

    ```
    """
    value = os.environ.get(_WARN_ONLY_ENV, "").strip().lower()
    if value in _WARN_ONLY_TRUE:
        return True
    if value in _WARN_ONLY_FALSE:
        return False
    msg = (
        f"Invalid value {os.environ[_WARN_ONLY_ENV]!r} for the environment variable "
        f"{_WARN_ONLY_ENV}. Use one of {sorted(_WARN_ONLY_TRUE | _WARN_ONLY_FALSE - {''})} "
        "(or leave it unset)"
    )
    raise ValueError(msg)


@hookimpl
def hatch_register_metadata_hook() -> type[MetadataHookInterface]:
    r"""Register the autoextras metadata hook with hatchling.

    This function is called by Hatchling's plugin system to register
    the AutoExtrasMetadataHook as a metadata hook plugin.

    Returns:
        The AutoExtrasMetadataHook class that implements the metadata
        hook interface.
    """
    return AutoExtrasMetadataHook
