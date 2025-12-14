#!/usr/bin/env bash

# check_markdown.sh - Validate markdown files with doctest
#
# Description:
#   This script finds and validates all markdown files in the repository
#   by running Python's doctest module on them. It ensures that any code
#   examples embedded in markdown documentation are correct and executable.
#   The script excludes virtual environments and cache directories.
#
# Usage:
#   ./check_markdown.sh
#
# Requirements:
#   - Python must be available in PATH
#   - doctest module (part of Python standard library)
#
# Doctest Options:
#   - NORMALIZE_WHITESPACE: Ignore differences in whitespace
#   - ELLIPSIS: Allow ... to match any substring
#   - REPORT_NDIFF: Show differences using ndiff format
#
# Exit Codes:
#   0 - All markdown files passed doctest validation
#   1 - One or more markdown files failed doctest validation

set -euo pipefail

# List of folders to exclude from markdown file search
exclude_folders=(.venv .pytest_cache)

# Build the find command with exclusions dynamically
find_cmd="find ."
for folder in "${exclude_folders[@]}"; do
	find_cmd+=" -path \"./$folder\" -prune -o"
done
find_cmd+=" -type f -name \"*.md\" -print"

# Execute the find command and capture the list of markdown files
files=$(eval "$find_cmd")
count=$(printf "%s\n" "$files" | awk 'END {print NR}')

echo "Found $count markdown files"

# Process each markdown file with doctest
printf "%s\n" "$files" | while IFS= read -r f; do
	echo "Checking: $f"
	python -m doctest -o NORMALIZE_WHITESPACE -o ELLIPSIS -o REPORT_NDIFF "$f"
done

echo "All $count markdown files have been checked"
