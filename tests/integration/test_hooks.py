from __future__ import annotations

import os
import subprocess
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping

# The integration projects install the hook from this checkout (not from PyPI),
# so the tests exercise the code of the working tree.
REPO_ROOT = Path(__file__).resolve().parents[2]
WARN_ONLY_ENV = "HATCHLING_AUTOEXTRAS_WARN_ONLY"


def run_uv_build(
    path: Path, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    r"""Run ``uv build`` in a project, without checking the result.

    uv does not detect the changes of the sources of a local directory
    (the cache key is ``pyproject.toml``), so the hook is refreshed to
    build with the current code.

    Args:
        path: The path of the project.
        env: Environment variables added to the environment of the build.

    Returns:
        The completed process, with the captured output.
    """
    return subprocess.run(
        ["uv", "build", "--refresh-package", "hatchling-autoextras-hook"],  # noqa: S607
        cwd=path,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


def build_minimal_project(path: Path, config: str = "", extra_extras: str = "") -> None:
    r"""Create a minimal project.

    Args:
        path: The path where to build the minimal project.
        config: Extra lines for the ``autoextras`` hook table.
        extra_extras: Extra lines for the optional dependencies table.
    """
    path.joinpath("pyproject.toml").write_text(
        f"""[build-system]
requires = ["hatchling", "hatchling-autoextras-hook @ {REPO_ROOT.as_uri()}"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.sdist]
only-include = ["src"]

[project]
name = "testpkg"
version = "0.1.0"
description = "Test project"
dynamic = ["maintainers"]
readme = "README.md"
requires-python = ">=3.11"

[project.optional-dependencies]
numpy = [ "numpy>=2.0" ]
dev = [ "pytest>=9.0" ]
{extra_extras}

[tool.hatch.metadata.hooks.autoextras]
{config}
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


def validate_metadata(metadata: str, group_name: str = "all") -> None:
    r"""Validate that the 'all' extra was automatically generated.

    Args:
        metadata: The content of the metadata file.
    """
    assert f"Provides-Extra: {group_name}" in metadata
    assert f"Requires-Dist: numpy>=2.0; extra == '{group_name}'" in metadata
    assert f"Requires-Dist: pytest>=9.0; extra == '{group_name}'" in metadata

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
    run_uv_build(path).check_returncode()
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


def test_autoextras_integration_custom_name(tmp_path: Path) -> None:
    r"""Build a temporary Python project using hatchling with the
    autoextras plugin and verify that the generated wheel contains an
    'all' extra that merges all optional dependencies."""
    path = tmp_path.joinpath("project")
    path.mkdir(exist_ok=True, parents=True)

    # ----------------------------------------------------------------------
    # 1. Create a minimal project that uses the autoextras metadata hook
    # ----------------------------------------------------------------------
    build_minimal_project(path, config='group-name = "complete"')
    # ----------------------------------------------------------------------
    # 2. Build the wheel using uv build
    # ----------------------------------------------------------------------
    run_uv_build(path).check_returncode()
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
    validate_metadata(metadata, group_name="complete")


def build_wheel_metadata(path: Path, config: str = "", extra_extras: str = "") -> str:
    r"""Build a project and return the wheel metadata."""
    path.mkdir(exist_ok=True, parents=True)
    build_minimal_project(path, config=config, extra_extras=extra_extras)
    run_uv_build(path).check_returncode()
    return read_metadata(find_wheel_path(path))


def build_project(
    path: Path,
    config: str = "",
    extra_extras: str = "",
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    r"""Build a project and return the result without checking it.

    Args:
        path: The path where to build the project.
        config: Extra lines for the ``autoextras`` hook table.
        extra_extras: Extra lines for the optional dependencies table.
        env: Environment variables added to the environment of the build.

    Returns:
        The completed process, with the captured output.
    """
    path.mkdir(exist_ok=True, parents=True)
    build_minimal_project(path, config=config, extra_extras=extra_extras)
    return run_uv_build(path, env)


def test_autoextras_integration_exclude(tmp_path: Path) -> None:
    r"""Excluded extras must not contribute to the combined group, but
    must still be provided as extras."""
    metadata = build_wheel_metadata(
        tmp_path / "project", config='group-name = "complete"\nexclude = ["dev"]'
    )
    assert "Provides-Extra: complete" in metadata
    assert "Requires-Dist: numpy>=2.0; extra == 'complete'" in metadata
    assert "Requires-Dist: pytest>=9.0; extra == 'complete'" not in metadata
    assert "Requires-Dist: pytest>=9.0; extra == 'dev'" in metadata


def test_autoextras_integration_existing_group_fails(tmp_path: Path) -> None:
    r"""The build must fail if the group exists and overwrite is not
    enabled."""
    path = tmp_path / "project"
    path.mkdir(parents=True)
    build_minimal_project(path, extra_extras='all = [ "old-dep" ]')
    result = run_uv_build(path)
    assert result.returncode != 0
    assert "already exists" in result.stdout + result.stderr


def test_autoextras_integration_overwrite(tmp_path: Path) -> None:
    r"""With overwrite enabled, the existing group is replaced."""
    metadata = build_wheel_metadata(
        tmp_path / "project", config="overwrite = true", extra_extras='all = [ "old-dep" ]'
    )
    validate_metadata(metadata)
    assert "old-dep" not in metadata


def test_autoextras_integration_unknown_option_fails(tmp_path: Path) -> None:
    r"""An unknown option must fail the build and name the option."""
    result = build_project(tmp_path / "project", config='excludes = ["dev"]')
    assert result.returncode != 0
    assert "Unknown option(s): ['excludes']" in result.stdout + result.stderr


def test_autoextras_integration_unknown_option_warn_only(tmp_path: Path) -> None:
    r"""With the warn-only variable, the build succeeds, warns, and the
    unknown option is ignored."""
    result = build_project(
        tmp_path / "project", config='excludes = ["dev"]', env={WARN_ONLY_ENV: "1"}
    )
    assert result.returncode == 0
    assert "Unknown option(s): ['excludes']" in result.stdout + result.stderr


def test_autoextras_integration_unknown_option_warn_only_metadata(tmp_path: Path) -> None:
    r"""The metadata built in warn-only mode is the one of a build
    without the unknown option."""
    build_project(tmp_path / "typo", config='excludes = ["dev"]', env={WARN_ONLY_ENV: "1"})
    expected = build_wheel_metadata(tmp_path / "clean")
    assert read_metadata(find_wheel_path(tmp_path / "typo")) == expected


def test_autoextras_integration_normalized_group_name(tmp_path: Path) -> None:
    r"""A group name that is not normalized is normalized by
    hatchling."""
    metadata = build_wheel_metadata(tmp_path / "project", config='group-name = "Full_Extra"')
    assert "Provides-Extra: full-extra" in metadata
    assert "Requires-Dist: numpy>=2.0; extra == 'full-extra'" in metadata
    assert "Requires-Dist: pytest>=9.0; extra == 'full-extra'" in metadata


def test_autoextras_integration_exclude_normalized(tmp_path: Path) -> None:
    r"""The excluded names are matched like hatchling does."""
    metadata = build_wheel_metadata(
        tmp_path / "project",
        config='exclude = ["DEV"]',
        extra_extras='my_extra = [ "rich>=13" ]',
    )
    assert "Requires-Dist: pytest>=9.0; extra == 'all'" not in metadata
    assert "Requires-Dist: rich>=13; extra == 'all'" in metadata


def test_autoextras_integration_existing_group_other_spelling_fails(tmp_path: Path) -> None:
    r"""An existing extra with another spelling of the name is a
    conflict, detected by the hook."""
    result = build_project(tmp_path / "project", extra_extras='All = [ "old-dep" ]')
    assert result.returncode != 0
    assert "Cannot create 'all' group: already exists" in result.stdout + result.stderr


def test_autoextras_integration_exclude_unmatched_fails(tmp_path: Path) -> None:
    r"""An ``exclude`` entry that matches no extra fails the build and
    is named in the error."""
    result = build_project(tmp_path / "project", config='exclude = ["tset"]')
    assert result.returncode != 0
    assert "'exclude' contains names that match no extra: ['tset']" in result.stdout + result.stderr


def test_autoextras_integration_exclude_unmatched_warn_only(tmp_path: Path) -> None:
    r"""With the warn-only variable, the unmatched entry warns and the
    METADATA is the one of the build without the entry."""
    result = build_project(
        tmp_path / "typo", config='exclude = ["dev", "tset"]', env={WARN_ONLY_ENV: "1"}
    )
    expected = build_wheel_metadata(tmp_path / "clean", config='exclude = ["dev"]')
    assert result.returncode == 0
    assert "match no extra: ['tset']" in result.stdout + result.stderr
    assert read_metadata(find_wheel_path(tmp_path / "typo")) == expected


def test_autoextras_integration_blank_dependency_fails(tmp_path: Path) -> None:
    r"""A blank dependency fails the build and names the source
    extra."""
    result = build_project(tmp_path / "project", extra_extras='docs = [ "sphinx", " " ]')
    assert result.returncode != 0
    assert "Dependency #2 of extra 'docs' must not be blank" in result.stdout + result.stderr


def test_autoextras_integration_self_reference(tmp_path: Path) -> None:
    r"""An extra that references the package is copied as is and resolved
    by hatchling: the generated extra contains the dependencies once."""
    metadata = build_wheel_metadata(
        tmp_path / "project", extra_extras='full = [ "testpkg[numpy]" ]'
    )
    assert metadata.count("Requires-Dist: numpy>=2.0; extra == 'all'") == 1


#######################################
#     Tests for validate_metadata     #
#######################################


def test_validate_metadata_valid() -> None:
    metadata = "\n".join(
        [
            "Metadata-Version: 2.4",
            "Name: testpkg",
            "Version: 0.1.0",
            "Dynamic: Maintainer",
            "Dynamic: Maintainer-email",
            "Summary: Test project",
            "Requires-Python: >=3.11",
            "Provides-Extra: all",
            "Requires-Dist: numpy>=2.0; extra == 'all'",
            "Requires-Dist: pytest>=9.0; extra == 'all'",
            "Provides-Extra: dev",
            "Requires-Dist: pytest>=9.0; extra == 'dev'",
            "Provides-Extra: numpy",
            "Requires-Dist: numpy>=2.0; extra == 'numpy'",
            "Description-Content-Type: text/markdown",
            "",
        ]
    )
    validate_metadata(metadata)


def test_validate_metadata_invalid() -> None:
    metadata = "\n".join(
        [
            "Metadata-Version: 2.4",
            "Name: testpkg",
            "Version: 0.1.0",
            "Dynamic: Maintainer",
            "Dynamic: Maintainer-email",
            "Summary: Test project",
            "Requires-Python: >=3.11",
            "Provides-Extra: dev",
            "Requires-Dist: pytest>=9.0; extra == 'dev'",
            "Provides-Extra: numpy",
            "Requires-Dist: numpy>=2.0; extra == 'numpy'",
            "Description-Content-Type: text/markdown",
            "",
        ]
    )
    with pytest.raises(AssertionError):
        validate_metadata(metadata)


def test_validate_metadata_empty() -> None:
    with pytest.raises(AssertionError):
        validate_metadata("")
