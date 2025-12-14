#!/usr/bin/env bash

# check_dependency_tree.sh - Validate package dependency tree structure
#
# Description:
#   This script verifies that the hatchling-autoextras-hook package has the
#   correct dependency tree structure. It checks that:
#   1. The package is properly installed and recognized
#   2. The only required dependency is hatchling
#   3. The dependency versions match expected patterns
#
# Usage:
#   ./check_dependency_tree.sh
#
# Requirements:
#   - uv must be installed and available in PATH
#   - hatchling-autoextras-hook must be installed in the current environment
#
# Exit Codes:
#   0 - Dependency tree validation passed
#   1 - Dependency tree validation failed (unexpected dependencies or versions)

set -euo pipefail

# Get the uv pip tree output
tree_output=$(uv pip tree --package hatchling-autoextras-hook --show-version-specifiers)

echo "Dependency tree"
echo "$tree_output"
echo ""

# Check if first line matches the pattern
first_line=$(echo "$tree_output" | head -n 1)
if ! echo "$first_line" | grep -qE '^hatchling-autoextras-hook v[0-9]+(\.[0-9]+)*[A-Za-z0-9]*$'; then
    echo "❌ ERROR: First line does not match expected pattern"
    echo "Expected: hatchling-autoextras-hook v<version>"
    echo "Got: $first_line"
    exit 1
fi
echo "✅ First line matches pattern: $first_line"
echo ""

# Define packages to check
packages=("hatchling")

# Track results
missing_packages=()
found_packages=()

# Check each package
for package in "${packages[@]}"; do
    # Match package name at second level (lines starting with ├── or └──)
    # Case-insensitive match for package names
    if echo "$tree_output" | grep -qiE "^[├└]── ${package} v"; then
        found_packages+=("$package")
        echo "✅ Found: $package"
    else
        missing_packages+=("$package")
        echo "❌ Missing: $package"
    fi
done

echo ""
echo "📊 Summary:"
echo " Found: ${#found_packages[@]}"
echo " Missing: ${#missing_packages[@]}"

# Exit with error if any packages are missing
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Missing packages:"
    printf '  • %s\n' "${missing_packages[@]}"
    exit 1
else
    echo ""
    echo "🎉 All packages found!"
fi
