# hatchling-autoextras-hook

<p align="center">
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/ci.yaml">
        <img alt="CI" src="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/ci.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/nightly-tests.yaml">
        <img alt="Nightly Tests" src="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/nightly-tests.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/nightly-package.yaml">
        <img alt="Nightly Package Tests" src="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/nightly-package.yaml/badge.svg">
    </a>
    <a href="https://codecov.io/gh/durandtibo/hatchling-autoextras-hook">
        <img alt="Codecov" src="https://codecov.io/gh/durandtibo/hatchling-autoextras-hook/branch/main/graph/badge.svg">
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

- Automatically combines all optional dependencies into a single extra
- Removes duplicates across extras and normalizes whitespace
- Sorts dependencies alphabetically for reproducible output
- Configurable group name, exclusion list, and overwrite behavior
- Validates its configuration and fails early with clear error messages
- Compatible with all Hatchling build targets (wheel, sdist)

## Configuration

All options are optional. Enabling the hook with an empty table is enough:

```toml
[tool.hatch.metadata.hooks.autoextras]
```

| Option       | Type      | Default | Description                                                         |
| ------------ | --------- | ------- | ------------------------------------------------------------------- |
| `group-name` | string    | `"all"` | Name of the generated extra. Must be a non-empty string.            |
| `exclude`    | list[str] | `[]`    | Names of extras that must not be included in the generated extra.   |
| `overwrite`  | boolean   | `false` | Replace an existing extra with the same name instead of raising.    |

Example:

```toml
[tool.hatch.metadata.hooks.autoextras]
group-name = "complete"
exclude = ["dev", "docs"]
overwrite = false
```

With this configuration, `pip install my-package[complete]` installs the dependencies of every
extra except `dev` and `docs`.

Regardless of the options, the hook:

- Leaves all original extras unchanged
- Never includes the generated extra itself in the list of collected dependencies
- Creates an empty extra if the project has no optional dependencies

### Errors

The build fails with an explicit message in the following cases:

| Situation                                                          | Exception      |
| ------------------------------------------------------------------ | -------------- |
| An extra named `group-name` already exists and `overwrite = false` | `RuntimeError` |
| `group-name` is not a non-empty string                             | `ValueError`   |
| `exclude` is not a list of strings                                 | `TypeError`    |
| `overwrite` is not a boolean                                       | `TypeError`    |
| `optional-dependencies` is not a table, or an extra is not a list  | `TypeError`    |

## Advanced Usage

### Using a Different Group Name

If `all` is already used by a hand-written extra, either pick another name with `group-name`, or
set `overwrite = true` to let the hook replace it.

### Excluding Extras

Use `exclude` to keep extras such as `dev`, `test`, or `docs` out of the combined extra:

```toml
[tool.hatch.metadata.hooks.autoextras]
exclude = ["dev", "test"]
```

### Using with Other Metadata Hooks

This hook is compatible with other Hatchling metadata hooks.

## Troubleshooting

### Hook Not Triggering

**Problem**: The generated extra is not present.

**Solutions**:

1. Ensure you have at least one dynamic field in your `[project]` section:

   ```toml
   [project]
   dynamic = ["version"]
   ```

   Hatchling metadata hooks only run when there are dynamic fields.

2. Verify the hook is listed in your `[build-system]`:

   ```toml
   [build-system]
   requires = ["hatchling>=1.18.0", "hatchling-autoextras-hook"]
   ```

3. Check that the hook configuration exists:

   ```toml
   [tool.hatch.metadata.hooks.autoextras]
   ```

### `Cannot create 'all' group: already exists`

**Problem**: The build raises a `RuntimeError` because an `all` extra is already defined.

**Solution**: Set `overwrite = true`, choose another `group-name`, or remove your manual `all`
extra.

### Dependencies Missing from the Generated Extra

**Problem**: Some dependencies are missing.

**Solutions**: Ensure the extras are defined in `[project.optional-dependencies]` (the hook does not
read `[dependency-groups]`), and check that they are not listed in `exclude`.

### Build Failures

**Problem**: The build fails with errors related to the hook.

**Solutions**:

1. Verify you are using Hatchling >= 1.18.0
2. Check the error message: it identifies the invalid option or extra
3. Check that your `pyproject.toml` syntax is correct
4. Build with verbose output: `python -m build -v`

## FAQ

### Q: Will this hook override my manually defined `all` extra?

**A:** No, not by default. The build fails with a `RuntimeError` so nothing is silently lost. Set
`overwrite = true` to replace it, or use a different `group-name`.

### Q: Can I exclude specific extras from being included in `all`?

**A:** Yes, use the `exclude` option.

### Q: Does this work with dependency groups (PEP 735)?

**A:** No. The hook only works with `[project.optional-dependencies]`. Dependency groups in
`[dependency-groups]` are not part of the package metadata.

### Q: Will this slow down my build process?

**A:** No, the hook only collects, deduplicates and sorts dependency strings.

### Q: Can I use this with Poetry or PDM?

**A:** No, the hook is specific to Hatchling.

### Q: How do I verify the hook is working?

**A:** Build your package and inspect the wheel metadata:

```bash
python -m build
unzip -p dist/your_package-*.whl '*/METADATA' | grep "Provides-Extra: all"
```

### Q: Does this hook modify my source files?

**A:** No, it only modifies the package metadata during the build. `pyproject.toml` is unchanged.

## Development

This project uses `uv` for dependency management. See [CONTRIBUTING.md](.github/CONTRIBUTING.md)
for setup instructions (`make setup-venv`) and [dev/README.md](dev/README.md) for development
scripts.

### Dependencies

| `hatchling-autoextras-hook` | `hatchling`   | `python`       |
| --------------------------- | ------------- | -------------- |
| `main`                      | `>=1.18,<2.0` | `>=3.10`       |
| `0.1.3`                     | `>=1.18,<2.0` | `>=3.10`       |
| `0.1.2`                     | `>=1.18,<2.0` | `>=3.10`       |
| `0.1.1`                     | `>=1.18,<2.0` | `>=3.10`       |
| `0.1.0`                     | `>=1.18,<2.0` | `>=3.10`       |
| `0.0.2`                     | `>=1.18,<2.0` | `>=3.10,<3.15` |
| `0.0.1`                     | `>=1.18,<2.0` | `>=3.10,<3.15` |

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

## Security

For information about security policies and how to report vulnerabilities, please see our
[Security Policy](SECURITY.md).

## License

`hatchling-autoextras-hook` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](LICENSE) file.
