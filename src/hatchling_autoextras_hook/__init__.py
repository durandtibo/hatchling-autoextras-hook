"""Hatchling metadata hook to automatically generate 'all' extras.

This package provides a Hatchling metadata hook that automatically creates
an 'all' extra in your project's optional dependencies, combining all
dependencies from all other extras.
"""

from __future__ import annotations

from hatchling_autoextras_hook.hooks import AutoExtrasMetadataHook

# NOTE: This version string should be kept in sync with the version in pyproject.toml
# Consider using dynamic versioning in a future release to avoid manual synchronization
__version__ = "0.0.3a0"
__all__ = ["AutoExtrasMetadataHook"]
