# hatchling-autoextras-hook

Hatchling metadata hook to automatically generate an `all` extra that combines all optional dependencies.

## Overview

This package provides a Hatchling metadata hook that automatically creates an `all` extra in your project's optional dependencies. The `all` extra will contain all dependencies from all other extras, making it easy for users to install all optional features at once.

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

**Important**: Hatchling metadata hooks are only triggered when there is at least one dynamic field in your project metadata. If you don't already have any dynamic fields, you can add `version` as a dynamic field:

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

### Setup

```bash
# Install uv
pip install uv

# Install dependencies
uv sync
```

### Running Tests

```bash
uv run pytest
```

## License

See LICENSE file for details.
