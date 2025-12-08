# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Fixed coverage configuration in pyproject.toml to use correct package name
- Fixed dependency table in README.md to show correct package name

### Added
- CHANGELOG.md file to track project changes
- SECURITY.md file with security policy

## [0.0.2] - Unreleased

### Added
- Initial release with metadata hook functionality
- Automatic generation of `all` extra from all optional dependencies
- Removal of duplicate dependencies
- Alphabetical sorting of dependencies

### Features
- Seamless integration with Hatchling build system
- Support for Python 3.10+
- Compatible with Hatchling 1.18+

## [0.0.1] - Unreleased

### Added
- Initial proof of concept

[Unreleased]: https://github.com/durandtibo/hatchling-autoextras-hook/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/durandtibo/hatchling-autoextras-hook/releases/tag/v0.0.2
[0.0.1]: https://github.com/durandtibo/hatchling-autoextras-hook/releases/tag/v0.0.1
