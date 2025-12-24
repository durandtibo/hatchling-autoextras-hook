r"""Hatchling metadata hook to automatically generate 'all' extras."""

from __future__ import annotations

from typing import Any

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.plugin import hookimpl


class AutoExtrasMetadataHook(MetadataHookInterface):
    r"""Metadata hook that automatically generates an 'all' extra.

    This hook collects all optional dependencies defined in the project
    and creates an 'all' extra that includes all of them.

    Example usage:

    ```pycon

    >>> from hatchling_autoextras_hook.hooks import AutoExtrasMetadataHook
    >>> metadata = {
    ...     "optional-dependencies": {
    ...         "dev": ["pytest>=7.0", "black>=22.0"],
    ...     }
    ... }
    >>> AutoExtrasMetadataHook("test", {}).update(metadata)
    >>> metadata
    {'optional-dependencies': {'dev': ['pytest>=7.0', 'black>=22.0'],
     'all': ['black>=22.0', 'pytest>=7.0']}}

    ```
    """

    PLUGIN_NAME: str = "autoextras"

    def update(self, metadata: dict[str, Any]) -> None:
        r"""Update the project metadata to add the configured extras
        group.

        This method collects all dependencies from all optional extras
        (excluding any existing group with the configured name), removes
        duplicates, sorts them alphabetically, and creates/updates the
        extras group with the combined list.

        Args:
            metadata: The project metadata dictionary to update. This
                dictionary is modified in place.

        Note:
            If no optional dependencies exist, this method does nothing.
            Any pre-existing extras group will be completely replaced.
        """
        # Get the configured extras group name (defaults to 'all')
        extras_group_name = self.config.get("group-name", "all")

        # Get optional dependencies
        optional_dependencies = metadata.get("optional-dependencies", {})

        if extras_group_name in optional_dependencies:
            msg = f"Group name '{extras_group_name}' already exists. Use a different group name."
            raise RuntimeError(msg)

        # Collect all dependencies from all extras (except the configured group if it exists)
        all_deps = set()
        for deps in optional_dependencies.values():
            all_deps.update(deps)

        # Add the extras group with all dependencies
        # Sort for consistent output
        optional_dependencies[extras_group_name] = sorted(all_deps)
        metadata["optional-dependencies"] = optional_dependencies


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
