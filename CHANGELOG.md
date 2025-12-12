# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added CHANGELOG.md to track version history
- Added .editorconfig for consistent code style across editors

### Changed
- Updated pytest configuration to use `[tool.pytest.ini_options]` format
- Improved workflow step naming in update-deps.yaml

### Removed
- Removed unnecessary torch-backend setting from pyproject.toml
- Removed non-existent conda target from Makefile

## [0.1.0] - 2024-XX-XX

### Added
- Initial release with automatic 'all' extras generation
- Support for Python 3.10+
- Comprehensive test suite
- Documentation and examples

### Features
- Automatically combines all optional dependencies
- Removes duplicates across extras
- Sorts dependencies alphabetically for consistency
- Works seamlessly with Hatchling build system
- Zero configuration required

## [0.0.2] - Previous release

## [0.0.1] - Initial release

[Unreleased]: https://github.com/durandtibo/hatchling-autoextras-hook/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/durandtibo/hatchling-autoextras-hook/releases/tag/v0.1.0
[0.0.2]: https://github.com/durandtibo/hatchling-autoextras-hook/releases/tag/v0.0.2
[0.0.1]: https://github.com/durandtibo/hatchling-autoextras-hook/releases/tag/v0.0.1
