# Development Scripts

This directory contains scripts and configurations used for development and CI/CD processes.

## Scripts

### check_markdown.sh
Validates markdown files for syntax and formatting issues.

**Usage:**
```bash
./dev/check_markdown.sh
```

### generate_versions.py
Generates and updates the package versions configuration file used for testing compatibility
with different versions of hatchling.

**Usage:**
```bash
python dev/generate_versions.py
```

**Output:** Creates/updates `dev/config/package_versions.json`

## Subdirectories

### config/
Contains configuration files for development tools and CI/CD processes.

- `package_versions.json`: List of hatchling versions to test against

### package/
Contains scripts for package validation and testing.

- `check_type.sh`: Runs type checking on the installed package
- `check_dependency_tree.sh`: Validates the dependency tree
- `check_metadata.sh`: Verifies package metadata is correct

## CI/CD Integration

These scripts are used by GitHub Actions workflows:

- `generate_versions.py` is called by `.github/workflows/generate-package-versions.yaml`
- Package check scripts are used in `.github/workflows/test-package*.yaml` workflows
- `check_markdown.sh` is called during doctest workflow

## Requirements

Some scripts require additional dependencies from the `dev` dependency group:

```bash
uv sync --group dev
```
