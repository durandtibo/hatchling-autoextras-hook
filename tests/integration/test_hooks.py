from __future__ import annotations

import subprocess
import zipfile
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def build_minimal_project(path: Path) -> None:
    r"""Create a minimal project.

    Args:
        path: The path where to build the minimal project.
    """
    path.joinpath("pyproject.toml").write_text(
        """[build-system]
requires = ["hatchling", "hatchling-autoextras-hook"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.sdist]
only-include = ["src"]

[tool.hatch.metadata.hooks.autoextras]

[project]
name = "testpkg"
version = "0.1.0"
description = "Test project"
dynamic = ["maintainers"]
readme = "README.md"
requires-python = ">=3.10"

[project.optional-dependencies]
numpy = [ "numpy>=2.0" ]
dev = [ "pytest>=9.0" ]
""",
        encoding="utf-8",
    )

    path.joinpath("README.md").write_text("Test package", encoding="utf-8")

    # Minimal module
    path_pkg = path.joinpath("src").joinpath("testpkg")
    path_pkg.mkdir(exist_ok=True, parents=True)
    path_pkg.joinpath("__init__.py").write_text("", encoding="utf-8")


def find_wheel_path(path: Path) -> Path:
    r"""Find the wheel path.

    Args:
        path: The project path.

    Returns:
        The wheel path.
    """
    dist_dir = path.joinpath("dist")
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, "Expected exactly one wheel"
    return wheels[0]


def read_metadata(path: Path) -> str:
    r"""Inspect wheel metadata, find the METADATA file inside the wheel,
    and read the content.

    Args:
        path: The path to the wheel.

    Returns:
        The content of the METADATA file.
    """
    with zipfile.ZipFile(path) as zf:
        namelist = zf.namelist()
        metadata_files = [n for n in namelist if n.endswith("METADATA")]
        assert metadata_files, "METADATA file not found in wheel"
        return zf.read(metadata_files[0]).decode()


def validate_metadata(metadata: str) -> None:
    r"""Validate that the 'all' extra was automatically generated.

    Args:
        metadata: The content of the metadata file.
    """
    assert "Provides-Extra: all" in metadata
    assert "Requires-Dist: numpy>=2.0; extra == 'all'" in metadata
    assert "Requires-Dist: pytest>=9.0; extra == 'all'" in metadata

    # Also ensure original extras still exist
    assert "Provides-Extra: numpy" in metadata
    assert "Provides-Extra: dev" in metadata


def test_autoextras_integration(tmp_path: Path) -> None:
    r"""Build a temporary Python project using hatchling with the
    autoextras plugin and verify that the generated wheel contains an
    'all' extra that merges all optional dependencies."""
    path = tmp_path.joinpath("project")
    path.mkdir(exist_ok=True, parents=True)

    # ----------------------------------------------------------------------
    # 1. Create a minimal project that uses the autoextras metadata hook
    # ----------------------------------------------------------------------
    build_minimal_project(path)
    # ----------------------------------------------------------------------
    # 2. Build the wheel using uv build
    # ----------------------------------------------------------------------
    subprocess.run(["uv", "build"], cwd=path, check=True)  # noqa: S607
    # ----------------------------------------------------------------------
    # 3. Find the generated wheel in dist/
    # ----------------------------------------------------------------------
    wheel_path = find_wheel_path(path)
    # ----------------------------------------------------------------------
    # 4. Inspect wheel metadata (METADATA file inside the .whl)
    # ----------------------------------------------------------------------
    metadata = read_metadata(wheel_path)
    # ----------------------------------------------------------------------
    # 5. Validate that the 'all' extra was automatically generated
    # ----------------------------------------------------------------------
    validate_metadata(metadata)


#######################################
#     Tests for validate_metadata     #
#######################################


def test_validate_metadata_valid() -> None:
    metadata = r"""Metadata-Version: 2.4
Name: testpkg
Version: 0.1.0
Dynamic: Maintainer
Dynamic: Maintainer-email
Summary: Test project
Requires-Python: >=3.10
Provides-Extra: all
Requires-Dist: numpy>=2.0; extra == 'all'
Requires-Dist: pytest>=9.0; extra == 'all'
Provides-Extra: dev
Requires-Dist: pytest>=9.0; extra == 'dev'
Provides-Extra: numpy
Requires-Dist: numpy>=2.0; extra == 'numpy'
Description-Content-Type: text/markdown
"""
    validate_metadata(metadata)


def test_validate_metadata_invalid() -> None:
    metadata = r"""Metadata-Version: 2.4
Name: testpkg
Version: 0.1.0
Dynamic: Maintainer
Dynamic: Maintainer-email
Summary: Test project
Requires-Python: >=3.10
Provides-Extra: dev
Requires-Dist: pytest>=9.0; extra == 'dev'
Provides-Extra: numpy
Requires-Dist: numpy>=2.0; extra == 'numpy'
Description-Content-Type: text/markdown
"""
    with pytest.raises(AssertionError):
        validate_metadata(metadata)


def test_validate_metadata_empty() -> None:
    with pytest.raises(AssertionError):
        validate_metadata("")
