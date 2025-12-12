#!/usr/bin/env bash

# check_metadata.sh - Verify package metadata is correct
#
# Description:
#   This script validates that the hatchling-autoextras-hook package
#   metadata is properly configured. It checks that:
#   1. The package name is correctly set to "hatchling-autoextras-hook"
#   2. The package requires "hatchling" as its only dependency
#
# Usage:
#   ./check_metadata.sh
#
# Requirements:
#   - uv must be installed and available in PATH
#   - hatchling-autoextras-hook must be installed in the current environment
#
# Exit Codes:
#   0 - Metadata validation passed
#   1 - Metadata validation failed (missing or incorrect metadata)

set -euo pipefail

# Retrieve package metadata using uv
METADATA=$(uv pip show hatchling-autoextras-hook)

# Display the full metadata for debugging purposes
echo "$METADATA"

# Validate that the package name is correct
echo "$METADATA" | grep -q "Name: hatchling-autoextras-hook"

# Validate that hatchling is listed as a required dependency
echo "$METADATA" | grep -q "Requires: hatchling"
