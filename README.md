# hatchling-autoextras-hook

<p align="center">
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions">
        <img alt="CI" src="https://github.com/durandtibo/hatchling-autoextras-hook/workflows/CI/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions">
        <img alt="Nightly Tests" src="https://github.com/durandtibo/hatchling-autoextras-hook/workflows/Nightly%20Tests/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions">
        <img alt="Nightly Package Tests" src="https://github.com/durandtibo/hatchling-autoextras-hook/workflows/Nightly%20Package%20Tests/badge.svg">
    </a>
    <a href="https://codecov.io/gh/durandtibo/hatchling-autoextras-hook">
        <img alt="Codecov" src="https://codecov.io/gh/durandtibo/hatchling-autoextras-hook/branch/main/graph/badge.svg">
    </a>
    <br/>
    <a href="https://durandtibo.github.io/hatchling-autoextras-hook/">
        <img alt="Documentation" src="https://github.com/durandtibo/hatchling-autoextras-hook/workflows/Documentation%20(stable)/badge.svg">
    </a>
    <a href="https://durandtibo.github.io/hatchling-autoextras-hook/">
        <img alt="Documentation" src="https://github.com/durandtibo/hatchling-autoextras-hook/workflows/Documentation%20(unstable)/badge.svg">
    </a>
    <br/>
    <a href="https://github.com/psf/black">
        <img  alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
    </a>
    <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/%20style-google-3666d6.svg">
    </a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;">
    </a>
    <a href="https://github.com/guilatrova/tryceratops">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/try%2Fexcept%20style-tryceratops%20%F0%9F%A6%96%E2%9C%A8-black">
    </a>
    <br/>
    <a href="https://pypi.org/project/hatchling-autoextras-hook/">
        <img alt="PYPI version" src="https://img.shields.io/pypi/v/hatchling-autoextras-hook">
    </a>
    <a href="https://pypi.org/project/hatchling-autoextras-hook/">
        <img alt="Python" src="https://img.shields.io/pypi/pyversions/hatchling-autoextras-hook.svg">
    </a>
    <a href="https://opensource.org/licenses/BSD-3-Clause">
        <img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/hatchling-autoextras-hook">
    </a>
    <br/>
    <a href="https://pepy.tech/project/hatchling-autoextras-hook">
        <img  alt="Downloads" src="https://static.pepy.tech/badge/hatchling-autoextras-hook">
    </a>
    <a href="https://pepy.tech/project/hatchling-autoextras-hook">
        <img  alt="Monthly downloads" src="https://static.pepy.tech/badge/hatchling-autoextras-hook/month">
    </a>
    <br/>

</p>

Hatchling metadata hook to automatically generate an `all` extra that combines all optional
dependencies.

## Overview

This package provides a [Hatchling](https://pypi.org/project/hatchling/) metadata hook that
automatically creates an `all` extra in your project's optional dependencies.
The `all` extra will contain all dependencies from all other extras, making it easy for users to
install all optional features at once.

## Installation

Add this package as a build dependency in your `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.18.0", "hatchling-autoextras-hook"]
build-backend = "hatchling.build"
```

## Usage

Enable the hook in your `pyproject.toml`:

```toml
[tool.hatch.metadata.hooks.autoextras]
```

**Important**: Hatchling metadata hooks are only triggered when there is at least one dynamic field
in your project metadata. If you don't already have any dynamic fields, you can add `version` as a
dynamic field:

```toml
[project]
name = "your-package"
dynamic = ["version"]

[tool.hatch.version]
path = "src/your_package/__init__.py"
```

Then add `__version__ = "x.y.z"` to your `__init__.py` file.

### Example

Given this configuration:

```toml
[build-system]
requires = ["hatchling>=1.18.0", "hatchling-autoextras-hook"]
build-backend = "hatchling.build"

[project]
name = "my-package"
dynamic = ["version"]

[project.optional-dependencies]
dev = ["pytest>=7.0", "black>=22.0"]
docs = ["sphinx>=5.0", "sphinx-rtd-theme>=1.0"]
typing = ["mypy>=1.0"]

[tool.hatch.version]
path = "src/my_package/__init__.py"

[tool.hatch.metadata.hooks.autoextras]
```

The hook will automatically generate an `all` extra combining all dependencies:

```toml
[project.optional-dependencies]
all = [
    "black>=22.0",
    "mypy>=1.0",
    "pytest>=7.0",
    "sphinx-rtd-theme>=1.0",
    "sphinx>=5.0",
]
# ... dev, docs, typing remain unchanged
```

Users can then install all optional dependencies with:

```bash
pip install your-package[all]
```

## Features

- Automatically combines all optional dependencies
- Removes duplicates across extras
- Sorts dependencies alphabetically for consistency
- Works seamlessly with the Hatchling build system

## Development

This project uses `uv` for dependency management.

### Dependencies

| `batcharray` | `hatchling`   | `python`       |
|--------------|---------------|----------------|
| `main`       | `>=1.18,<2.0` | `>=3.10,<3.15` |
| `0.0.2`      | `>=1.18,<2.0` | `>=3.10,<3.15` |
| `0.0.1`      | `>=1.18,<2.0` | `>=3.10,<3.15` |

## Contributing

Please check the instructions in [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## Suggestions and Communication

Everyone is welcome to contribute to the community.
If you have any questions or suggestions, you can
submit [Github Issues](https://github.com/durandtibo/hatchling-autoextras-hook/issues).
We will reply to you as soon as possible. Thank you very much.

## API stability

:warning: While `hatchling-autoextras-hook` is in development stage, no API is guaranteed to be
stable from one release to the next.
In fact, it is very likely that the API will change multiple times before a stable 1.0.0 release.
In practice, this means that upgrading `hatchling-autoextras-hook` to a new version will possibly
break any code that was using the old version of `hatchling-autoextras-hook`.

## License

`hatchling-autoextras-hook` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](LICENSE) file.
