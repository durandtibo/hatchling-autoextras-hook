#!/usr/bin/env bash

set -euo pipefail

METADATA=$(uv pip show hatchling-autoextras-hook)

echo "$METADATA"

echo "$METADATA" | grep -q "Name: hatchling-autoextras-hook"
echo "$METADATA" | grep -q "Requires: hatchling"
