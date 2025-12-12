#!/usr/bin/env bash

# check_type.sh - Verify package type checking with pyright
#
# Description:
#   This script validates that the hatchling-autoextras-hook package is
#   properly typed and can be successfully analyzed by pyright. It creates
#   a temporary test file that imports the package and runs pyright to
#   ensure type annotations are correct and the package is recognized as typed.
#
# Usage:
#   ./check_type.sh
#
# Requirements:
#   - pyright must be installed and available in PATH
#   - hatchling-autoextras-hook must be installed in the current environment
#
# Exit Codes:
#   0 - Type checking passed successfully
#   1 - Type checking failed or pyright encountered errors

set -euo pipefail

# Directory for temporary pyright test files
PYRIGHT_DIR=tmp/pyright_check
mkdir -p "$PYRIGHT_DIR"

# Ensure cleanup on exit, even on error
cleanup() {
  rm -rf "$PYRIGHT_DIR"
}
trap cleanup EXIT

# Create pyright test file that imports the hook and creates an instance to verify typing
cat >"$PYRIGHT_DIR/check_pyright_import.py" <<'EOF'
from hatchling_autoextras_hook import AutoExtrasMetadataHook

hook = AutoExtrasMetadataHook(root="test", config={})
EOF

# Check that pyright recognizes the package as typed
pyright "$PYRIGHT_DIR"
