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

# Get the dependency tree for the package
OUTPUT=$(uv pip tree --package hatchling-autoextras-hook --show-version-specifiers)
echo "$OUTPUT"

# Define expected patterns for each line (in order)
# Line 1: Package name and version
# Line 2: The only dependency should be hatchling
PATTERNS=(
  '^hatchling-autoextras-hook v[0-9]+(\.[0-9]+)*[A-Za-z0-9]*$'
  '^└── hatchling v[0-9]+(\.[0-9]+)*[[:space:]]+\[required:.*\]$'
)

# Number of lines we want to check
MAX_LINES=${#PATTERNS[@]}

# --- Validator ---
# Iterate through each line and validate against expected patterns
i=1
while IFS= read -r line; do
    # Stop once all patterns have been checked
    if (( i > MAX_LINES )); then
        break
    fi

    pattern="${PATTERNS[$((i-1))]}"

    # Check if the line matches the expected pattern
    if ! [[ "$line" =~ $pattern ]]; then
        echo "❌ Line $i does NOT match expected pattern"
        echo "   Line content:    '$line'"
        echo "   Expected pattern: $pattern"
        exit 1
    fi

    ((i++))
done <<< "$OUTPUT"

echo "✅ First $MAX_LINES lines match."
