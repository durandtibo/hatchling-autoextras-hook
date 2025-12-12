# Development Scripts

This directory contains scripts and configurations used for development, testing, and CI/CD processes.

## Scripts

### check_markdown.sh

Validates markdown files by running Python's doctest on code examples embedded in the documentation.

**Purpose:**
- Ensures code examples in markdown files are accurate and executable
- Catches outdated examples that may break after code changes
- Validates all `.md` files except those in excluded directories (`.venv`, `.pytest_cache`)

**Usage:**

```bash
./dev/check_markdown.sh
```

**Requirements:**
- Python with doctest module (standard library)

**Exit Codes:**
- `0`: All markdown files passed validation
- `1`: One or more files failed validation

---

### generate_versions.py

Generates and updates the package versions configuration file used for testing compatibility
with different versions of hatchling.

**Purpose:**
- Fetches the latest minor versions of hatchling (>= 1.18)
- Creates/updates `dev/config/package_versions.json` for CI/CD matrix testing
- Ensures the package is tested against multiple hatchling versions

**Usage:**

```bash
python dev/generate_versions.py
```

**Output:** Creates/updates `dev/config/package_versions.json`

**Requirements:**
- Python with `feu` package installed (`uv sync --group dev`)

---

## Subdirectories

### config/

Contains configuration files for development tools and CI/CD processes.

**Files:**
- `package_versions.json`: List of hatchling versions to test against in CI/CD workflows

---

### package/

Contains scripts for package validation and testing. These scripts verify that the installed
package meets quality requirements.

#### check_type.sh

Validates that the package is properly typed and recognized by pyright.

**Purpose:**
- Creates a temporary test file that imports the package
- Runs pyright to verify type annotations are correct
- Ensures the package is recognized as a typed package

**Usage:**

```bash
./dev/package/check_type.sh
```

**Requirements:**
- `pyright` installed
- `hatchling-autoextras-hook` installed in current environment

**Exit Codes:**
- `0`: Type checking passed
- `1`: Type checking failed

---

#### check_dependency_tree.sh

Validates the dependency tree structure of the installed package.

**Purpose:**
- Verifies the package has only the expected dependency (hatchling)
- Checks version patterns match expected format
- Ensures no unexpected dependencies were introduced

**Usage:**

```bash
./dev/package/check_dependency_tree.sh
```

**Requirements:**
- `uv` installed
- `hatchling-autoextras-hook` installed in current environment

**Exit Codes:**
- `0`: Dependency tree validation passed
- `1`: Unexpected dependencies or versions found

---

#### check_metadata.sh

Verifies package metadata is correctly configured.

**Purpose:**
- Validates package name is "hatchling-autoextras-hook"
- Confirms hatchling is listed as a required dependency
- Ensures metadata integrity

**Usage:**

```bash
./dev/package/check_metadata.sh
```

**Requirements:**
- `uv` installed
- `hatchling-autoextras-hook` installed in current environment

**Exit Codes:**
- `0`: Metadata validation passed
- `1`: Missing or incorrect metadata

---

#### custom_checks.sh

Runs custom package validation checks defined in the test suite.

**Purpose:**
- Executes project-specific validation not covered by standard checks
- Runs tests defined in `tests/package_checks.py`
- Validates package installation and basic functionality

**Usage:**

```bash
./dev/package/custom_checks.sh
```

**Requirements:**
- Python installed
- `hatchling-autoextras-hook` installed in current environment
- `tests/package_checks.py` exists

**Exit Codes:**
- `0`: Custom checks passed
- `1`: Custom checks failed

---

## CI/CD Integration

These scripts are integrated into GitHub Actions workflows for automated testing:

| Script | Workflow | Purpose |
|--------|----------|---------|
| `generate_versions.py` | `.github/workflows/generate-package-versions.yaml` | Generate version matrix for testing |
| `package/check_*.sh` | `.github/workflows/build.yaml` | Package validation after build |
| `check_markdown.sh` | Doctest workflow | Validate markdown documentation |
| `tests/package_checks.py` | `.github/workflows/test-package*.yaml` | Package installation tests |

## Requirements

Most scripts require dependencies from the `dev` dependency group:

```bash
# Install all development dependencies
uv sync --group dev

# Or using the project's invoke tasks
make install-all
```

## Best Practices

When adding new validation scripts:

1. Include a comprehensive header comment explaining purpose, usage, requirements, and exit codes
2. Use `set -euo pipefail` for bash scripts to fail fast on errors
3. Add shellcheck validation to ensure script quality
4. Document the script in this README
5. Add the script to relevant CI/CD workflows if applicable
