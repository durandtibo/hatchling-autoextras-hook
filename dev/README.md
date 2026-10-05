# Development Scripts

This directory contains scripts and configurations used for development, testing, and CI/CD processes.

## Scripts

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

## CI/CD Integration

These scripts are integrated into GitHub Actions workflows for automated testing:

| Script                    | Workflow                                           | Purpose                             |
| ------------------------- | -------------------------------------------------- | ----------------------------------- |
| `generate_versions.py`    | `.github/workflows/generate-package-versions.yaml` | Generate version matrix for testing |
| `tests/package_checks.py` | `.github/workflows/test-package*.yaml`             | Package installation tests          |

## Requirements

Most scripts require dependencies from the `dev` dependency group:

```bash
# Install all development dependencies
uv sync --group dev

# Or using the project's invoke tasks
make install-all
```
