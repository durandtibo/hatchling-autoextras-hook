# hatchling-autoextras-hook

<!-- markdownlint-disable MD013 -->
<p align="center">
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/ci.yaml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/durandtibo/hatchling-autoextras-hook/ci.yaml?branch=main&label=CI&logo=github"></a>
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/actions/workflows/nightly-package.yaml"><img alt="Nightly Package Tests" src="https://img.shields.io/github/actions/workflow/status/durandtibo/hatchling-autoextras-hook/nightly-package.yaml?label=nightly&logo=github"></a>
    <a href="https://codecov.io/gh/durandtibo/hatchling-autoextras-hook"><img alt="Codecov" src="https://img.shields.io/codecov/c/github/durandtibo/hatchling-autoextras-hook?logo=codecov"></a>
    <a href="https://durandtibo.github.io/hatchling-autoextras-hook/"><img alt="Documentation (stable)" src="https://img.shields.io/badge/docs-stable-blue?logo=readthedocs&logoColor=white"></a>
    <br/>
    <a href="https://pypi.org/project/hatchling-autoextras-hook/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/hatchling-autoextras-hook?logo=pypi&logoColor=white"></a>
    <a href="https://pypi.org/project/hatchling-autoextras-hook/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/hatchling-autoextras-hook?logo=python&logoColor=white"></a>
    <a href="https://opensource.org/licenses/BSD-3-Clause"><img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/hatchling-autoextras-hook"></a>
    <br/>
    <a href="https://github.com/astral-sh/ruff"><img alt="Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
    <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings"><img alt="Doc style: google" src="https://img.shields.io/badge/docstyle-google-3666d6"></a>
    <a href="https://scorecard.dev/viewer/?uri=github.com/durandtibo/hatchling-autoextras-hook"><img alt="OpenSSF Scorecard" src="https://img.shields.io/ossf-scorecard/github.com/durandtibo/hatchling-autoextras-hook?label=openssf%20scorecard"></a>
    <br/>
    <a href="https://pepy.tech/project/hatchling-autoextras-hook"><img alt="Downloads" src="https://img.shields.io/pepy/dt/hatchling-autoextras-hook"></a>
    <a href="https://pepy.tech/project/hatchling-autoextras-hook"><img alt="Monthly downloads" src="https://img.shields.io/pepy/dm/hatchling-autoextras-hook"></a>
    <a href="https://github.com/durandtibo/hatchling-autoextras-hook/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/durandtibo/hatchling-autoextras-hook?logo=github"></a>
</p>
<!-- markdownlint-enable MD013 -->

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
- Validates its configuration (unknown options included) and fails early with clear error messages
- Compatible with all Hatchling build targets (wheel, sdist)

## Properties

These are the guarantees of the hook:

| Property                | Statement                                                                                                                                      |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Union of the extras     | The generated extra contains every dependency of every non-excluded extra, and nothing else. It never contains its own previous content.       |
| Deterministic           | The output is the sorted list of the distinct dependency strings, whatever the order of the extras.                                            |
| Additive                | Original extras are never modified, reordered or removed. Only the generated extra is added (or replaced when `overwrite = true`).             |
| Atomic                  | The hook either completes or raises with the metadata unchanged.                                                                               |
| Name-normalized         | Extra names are compared after the normalization of PEP 685 (`Dev_Extra`, `dev-extra` and `dev.extra` are the same extra).                      |
| Strict                  | By default, an unknown option, a wrong type, an invalid name, a non-string or blank dependency, and an `exclude` entry that matches no extra raise. |
| Lenient on request      | With `HATCHLING_AUTOEXTRAS_WARN_ONLY=1`, the unknown options and the unmatched `exclude` entries warn. Every other problem still raises.        |
| Early and named errors  | Configuration errors are raised before any metadata is read. Metadata errors name the extra and the position of the faulty entry.              |
| Pure                    | No file access, no global state, no state kept between calls. The only environment variable read is `HATCHLING_AUTOEXTRAS_WARN_ONLY`.          |
| Minimal                 | One runtime dependency (`hatchling`), one hook, three options.                                                                                 |
| Observable              | What was generated is logged at `DEBUG` level.                                                                                                 |

Not guaranteed:

- **Validity of a requirement.** The hook does not parse requirements. A string that is not a valid
  PEP 508 requirement is copied as is and rejected by Hatchling afterwards.
- **Semantic deduplication.** `numpy>=2` and `numpy >= 2` are two strings, so they are two entries of
  the generated extra. Hatchling merges them when it normalizes the metadata.
- **PEP 735 dependency groups**, `dynamic = ["optional-dependencies"]` and the Hatchling option
  `allow-ambiguous-features`.

## Configuration

All options are optional. Enabling the hook with an empty table is enough:

```toml
[tool.hatch.metadata.hooks.autoextras]
```

| Option       | Type      | Default | Description                                                       |
| ------------ | --------- | ------- | ----------------------------------------------------------------- |
| `group-name` | string    | `"all"` | Name of the generated extra. Must be a valid extra name.          |
| `exclude`    | list[str] | `[]`    | Names of extras that must not be included in the generated extra. |
| `overwrite`  | boolean   | `false` | Replace an existing extra with the same name instead of raising.  |

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
- Rejects non-string and blank dependency entries (the error names the extra and the position)
- Creates an empty extra if the project has no optional dependencies
- Logs what it generated at `DEBUG` level

### Option details

#### `group-name`

Name of the extra that the hook generates (default: `"all"`). Users install it with
`pip install my-package[<group-name>]`. The value must be a valid extra name (letters, digits, `-`,
`_` and `.`, starting and ending with a letter or a digit, no whitespace), otherwise a `ValueError`
is raised (a `TypeError` if it is not a string). Names are compared after the normalization of
[PEP 685](https://peps.python.org/pep-0685/), like Hatchling does: `Full_Extra`, `full-extra` and
`full.extra` are the same extra.

```toml
[tool.hatch.metadata.hooks.autoextras]
group-name = "complete"
```

```toml
[project.optional-dependencies]
dev = ["pytest>=7.0"]
docs = ["sphinx>=5.0"]
complete = ["pytest>=7.0", "sphinx>=5.0"]  # generated
```

Use it when `all` is already taken by a hand-written extra, or when you prefer another name such as
`full` or `complete`. If an extra with this name already exists, see [`overwrite`](#overwrite).

#### `exclude`

List of extra names to leave out of the generated extra (default: `[]`). The excluded extras remain
available on their own; only their dependencies are not copied into the generated extra.

```toml
[tool.hatch.metadata.hooks.autoextras]
exclude = ["dev", "docs"]
```

```toml
[project.optional-dependencies]
dev = ["pytest>=7.0"]
docs = ["sphinx>=5.0"]
aws = ["boto3>=1.0"]
all = ["boto3>=1.0"]  # generated: dev and docs are excluded
```

Notes:

- Names are compared after the normalization of PEP 685: `exclude = ["B.c"]` excludes `B_c`, and
  `exclude = ["A"]` excludes `a` (see the matching rules in the [Properties](#properties)).
- The generated extra cannot be excluded (`ValueError`).
- A name that matches no extra raises a `ValueError` (a typo would otherwise put the dependencies
  of an extra you wanted to exclude into the generated extra). With
  `HATCHLING_AUTOEXTRAS_WARN_ONLY=1` it emits a `UserWarning` and has no effect.
- A dependency that also appears in a non-excluded extra is still included.
- The value must be a list of strings, otherwise a `TypeError` is raised.

#### `overwrite`

Boolean (default: `false`) controlling what happens when an extra named `group-name` already exists
in `[project.optional-dependencies]` (the names are compared normalized, so `All` conflicts with `all`).

- `false`: the build fails with a `ValueError`, so a hand-written extra is never lost silently.
- `true`: the existing extra is replaced by the generated one. Its previous content is **not**
  merged: it is ignored when collecting dependencies and discarded.

```toml
[project.optional-dependencies]
dev = ["pytest>=7.0"]
all = ["numpy"]  # hand-written

[tool.hatch.metadata.hooks.autoextras]
overwrite = true
# result: all = ["pytest>=7.0"]
```

The value must be a boolean (`true`/`false`, not a string), otherwise a `TypeError` is raised.

### Errors

The build fails with an explicit message in the following cases:

| Situation                                                          | Exception    | Warn-only mode |
| ------------------------------------------------------------------ | ------------ | -------------- |
| The hook table contains an unknown option                          | `ValueError` | warning        |
| `exclude` has a name that matches no extra                         | `ValueError` | warning        |
| An extra named `group-name` already exists and `overwrite = false` | `ValueError` | error          |
| `group-name` is not a valid extra name                             | `ValueError` | error          |
| `group-name` is not a string                                       | `TypeError`  | error          |
| `exclude` contains the generated extra                             | `ValueError` | error          |
| `exclude` is not a list of strings                                 | `TypeError`  | error          |
| `overwrite` is not a boolean                                       | `TypeError`  | error          |
| `optional-dependencies` is not a table, or an extra is not a list  | `TypeError`  | error          |
| A dependency of an extra is not a string                           | `TypeError`  | error          |
| A dependency of an extra is blank                                  | `ValueError` | error          |
| `HATCHLING_AUTOEXTRAS_WARN_ONLY` has an unrecognized value         | `ValueError` | error          |

### Strict and warn-only modes

Unknown options (for example `excludes` instead of `exclude`) and `exclude` entries that match no
extra fail the build, because a typo would otherwise be ignored silently. A person who builds a
project they do not control can downgrade these two problems to a `UserWarning` with an
environment variable, which is read when the hook is created:

```bash
HATCHLING_AUTOEXTRAS_WARN_ONLY=1 python -m build
```

Accepted values (case-insensitive): `1`, `true`, `yes`, `on` enable the warn-only mode; `0`,
`false`, `no`, `off`, an empty value or an unset variable keep the strict mode. Any other value
raises a `ValueError`. The unknown option and the unmatched `exclude` entry are ignored in the
warn-only mode. Every other problem still raises.

## Advanced Usage

### Combining Options

```toml
[tool.hatch.metadata.hooks.autoextras]
group-name = "full"
exclude = ["dev", "test"]
overwrite = true
```

### Using with Other Metadata Hooks

The interaction with other metadata hooks, and with `dynamic = ["optional-dependencies"]`, is not
specified: the hook only sees the static `optional-dependencies` table. Check the built metadata
with your Hatchling version if you combine them.

### Python API

The hook can also be used directly, which is mostly useful for testing:

```python
from hatchling_autoextras_hook.hooks import AutoExtrasMetadataHook

metadata = {"optional-dependencies": {"dev": ["pytest>=7.0", "black>=22.0"]}}
hook = AutoExtrasMetadataHook("root", {"group-name": "complete"})
hook.update(metadata)  # modifies `metadata` in place
```

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

### `Cannot create the 'all' extra: 'all' already exists`

**Problem**: The build raises a `ValueError` because an `all` extra is already defined (the message
names the existing extra, whatever its spelling: `All`, `a_ll`, ...).

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

**A:** No, not by default. The build fails with a `ValueError` so nothing is silently lost. Set
`overwrite = true` to replace it, or use a different `group-name`.

### Q: Why does the build fail on a typo?

**A:** A typo in an option name (`excludes`) or in an `exclude` entry (`tset`) would otherwise be
ignored silently, and the dependencies of an extra you meant to exclude (often `dev` or `test`) would
end up in the public generated extra. The hook fails and names the culprit. To downgrade the unknown
options and the unmatched `exclude` entries to warnings, set `HATCHLING_AUTOEXTRAS_WARN_ONLY=1` in
the environment of the build (see [Strict and warn-only modes](#strict-and-warn-only-modes)).

### Q: Can I exclude specific extras from being included in `all`?

**A:** Yes, use the [`exclude`](#exclude) option.

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
| `main`                      | `>=1.18,<2.0` | `>=3.11`       |
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
