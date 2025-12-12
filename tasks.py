r"""Define some tasks that are executed with invoke."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invoke.tasks import task

if TYPE_CHECKING:
    from invoke.context import Context

NAME = "hatchling_autoextras_hook"
SOURCE = f"src/{NAME}"
TESTS = "tests"
UNIT_TESTS = f"{TESTS}/unit"
INTEGRATION_TESTS = f"{TESTS}/integration"
PYTHON_VERSION = "3.13"


@task
def check_format(c: Context) -> None:
    r"""Check code format with black.

    Args:
        c: The invoke context.
    """
    c.run("black --check .", pty=True)


@task
def check_lint(c: Context) -> None:
    r"""Check code linting with ruff.

    Args:
        c: The invoke context.
    """
    c.run("ruff check --output-format=github .", pty=True)


@task
def check_types(c: Context) -> None:
    r"""Check type hints with pyright.

    Args:
        c: The invoke context.
    """
    c.run("pyright .", pty=True)


@task
def create_venv(c: Context) -> None:
    r"""Create a virtual environment and install invoke.

    Args:
        c: The invoke context.
    """
    c.run(f"uv venv --python {PYTHON_VERSION} --clear", pty=True)
    c.run("source .venv/bin/activate", pty=True)
    c.run("make install-invoke", pty=True)


@task
def doctest_src(c: Context) -> None:
    r"""Run doctests on source code and validate markdown code examples.

    This function performs two types of validation:
    1. Runs doctests on Python source code files using xdoctest
    2. Validates code examples embedded in markdown files using Python's doctest

    Args:
        c: The invoke context.
    """
    c.run(f"python -m pytest --xdoctest {SOURCE}", pty=True)
    c.run("dev/check_markdown.sh", pty=True)


@task
def docformat(c: Context) -> None:
    r"""Format docstrings in source code.

    Args:
        c: The invoke context.
    """
    c.run(f"docformatter --config ./pyproject.toml --in-place {SOURCE}", pty=True)


@task
def install(c: Context, optional_deps: bool = True, dev_deps: bool = True) -> None:
    r"""Install project dependencies and the package in editable mode.

    Args:
        c: The invoke context.
        optional_deps: If True, install all optional dependencies.
        dev_deps: If True, install development dependencies.
    """
    cmd = ["uv sync --frozen"]
    if optional_deps:
        cmd.append("--all-extras")
    if dev_deps:
        cmd.append("--group dev")
    c.run(" ".join(cmd), pty=True)
    c.run("uv pip install -e .", pty=True)


@task
def update(c: Context) -> None:
    r"""Update the dependencies and pre-commit hooks.

    Args:
        c: The invoke context.
    """
    c.run("uv sync --upgrade", pty=True)
    c.run("uv tool upgrade --all", pty=True)
    c.run("pre-commit autoupdate", pty=True)
    install(c)


@task
def all_test(c: Context, cov: bool = False) -> None:
    r"""Run all tests (unit and integration).

    Args:
        c: The invoke context.
        cov: If True, generate coverage reports.
    """
    cmd = ["python -m pytest --xdoctest --timeout 10"]
    if cov:
        cmd.append(f"--cov-report html --cov-report xml --cov-report term --cov={NAME}")
    cmd.append(f"{TESTS}")
    c.run(" ".join(cmd), pty=True)


@task
def unit_test(c: Context, cov: bool = False) -> None:
    r"""Run unit tests.

    Args:
        c: The invoke context.
        cov: If True, generate coverage reports.
    """
    cmd = ["python -m pytest --xdoctest --timeout 10"]
    if cov:
        cmd.append(f"--cov-report html --cov-report xml --cov-report term --cov={NAME}")
    cmd.append(f"{UNIT_TESTS}")
    c.run(" ".join(cmd), pty=True)


@task
def integration_test(c: Context, cov: bool = False) -> None:
    r"""Run integration tests.

    Args:
        c: The invoke context.
        cov: If True, generate coverage reports.
    """
    cmd = ["python -m pytest --xdoctest --timeout 60"]
    if cov:
        cmd.append(
            f"--cov-report html --cov-report xml --cov-report term  --cov-append --cov={NAME}"
        )
    cmd.append(f"{INTEGRATION_TESTS}")
    c.run(" ".join(cmd), pty=True)


@task
def show_installed_packages(c: Context) -> None:
    r"""Show the installed packages.

    Args:
        c: The invoke context.
    """
    c.run("uv pip list", pty=True)


@task
def show_python_config(c: Context) -> None:
    r"""Show the python configuration.

    Args:
        c: The invoke context.
    """
    c.run("uv python list --only-installed", pty=True)
    c.run("uv python find", pty=True)
    c.run("which python", pty=True)


@task
def publish_pypi(c: Context) -> None:
    r"""Publish the package to PyPI.

    Args:
        c: The invoke context.
    """
    c.run("uv build", pty=True)
    c.run(
        f'uv run --with {NAME} --refresh-package {NAME} --no-project -- python -c "import {NAME}"',
        pty=True,
    )
    c.run("uv publish --token ${PYPI_TOKEN}", pty=True)
