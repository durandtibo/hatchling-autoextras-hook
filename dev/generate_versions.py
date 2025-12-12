# noqa: INP001
r"""Script to create or update the package versions."""

from __future__ import annotations

import logging
from pathlib import Path

from feu.utils.io import save_json
from feu.version import get_latest_minor_versions

logger = logging.getLogger(__name__)


def get_package_versions() -> dict[str, list[str]]:
    r"""Get the latest minor versions for each package dependency.

    This function retrieves the latest minor versions of hatchling
    starting from version 1.18, which is the minimum required version
    for this project.

    Returns:
        A dictionary mapping package names to lists of version strings.
        Currently only contains versions for "hatchling".
    """
    return {"hatchling": list(get_latest_minor_versions("hatchling", lower="1.18"))}


def main() -> None:
    r"""Generate the package versions and save them in a JSON file.

    This function:
    1. Retrieves the latest minor versions for package dependencies
    2. Logs the versions for debugging
    3. Saves them to dev/config/package_versions.json

    The generated file is used by CI/CD workflows to test against
    multiple versions of dependencies.
    """
    versions = get_package_versions()
    logger.info(f"{versions=}")
    path = Path(__file__).parent.parent.joinpath("dev/config").joinpath("package_versions.json")
    logger.info(f"Saving package versions to {path}")
    save_json(versions, path, exist_ok=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
