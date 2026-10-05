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

---

## CI/CD Integration

These scripts are integrated into GitHub Actions workflows for automated testing:

| Script                    | Workflow                                           | Purpose                             |
| ------------------------- | -------------------------------------------------- | ----------------------------------- |
| `generate_versions.py`    | `.github/workflows/generate-package-versions.yaml` | Generate version matrix for testing |
| `check_markdown.sh`       | Doctest workflow                                   | Validate markdown documentation     |
| `tests/package_checks.py` | `.github/workflows/test-package*.yaml`             | Package installation tests          |

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
