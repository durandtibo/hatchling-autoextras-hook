# Contributing to `hatchling-autoextras-hook`

We want to make contributing to this project as easy and transparent as possible.

## Overview

We welcome contributions from anyone, even if you are new to open source.

- If you are planning to contribute back bug-fixes, please do so without any further discussion.
- If you plan to contribute new features, utility functions, or extensions to the core, please first
  open an issue and discuss the feature with us.
- For documentation improvements, typo fixes, or small enhancements, feel free to submit a PR directly.

Once you implement and test your feature or bug-fix, please submit a Pull Request.

## Types of Contributions

We welcome many types of contributions:

- **Bug fixes**: Fix issues identified in the issue tracker or that you've discovered
- **Features**: Add new functionality to the metadata hook
- **Documentation**: Improve README, add examples, fix typos, enhance API documentation
- **Tests**: Add test coverage, improve existing tests, add integration tests
- **Performance**: Optimize existing code for better performance
- **Code quality**: Refactoring, better error messages, type hints improvements

## Development Setup

Before you start contributing, set up your development environment:

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/hatchling-autoextras-hook.git
cd hatchling-autoextras-hook

# Install uv if you don't have it (see https://docs.astral.sh/uv/getting-started/installation/)

# Set up the development environment
make setup-venv

# Activate the virtual environment
source .venv/bin/activate
```

## Pull Requests

We actively welcome your pull requests.

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b my-feature-branch
   ```

2. If you've added code that should be tested, add tests:
   - Unit tests go in `tests/unit/`
   - Integration tests go in `tests/integration/`

3. If you've changed APIs or added features, update the documentation:
   - Update docstrings in the code
   - Update README.md if user-facing changes
   - Add examples if introducing new functionality

4. Ensure the test suite passes:
   ```bash
   # Run unit tests
   inv unit-test --cov
   
   # Run integration tests
   inv integration-test
   
   # Run both with coverage report
   inv unit-test --cov && inv integration-test --cov
   ```

5. Make sure your code lints and is properly formatted:
   ```bash
   # Run pre-commit hooks
   pre-commit run --all-files
   
   # Or run individual tools
   inv check-format  # Check formatting
   inv check-lint    # Check linting
   ```

6. Commit your changes with a clear and descriptive commit message:
   ```bash
   git commit -m "Add feature: brief description of what was added"
   ```

7. Push to your fork and submit a pull request:
   ```bash
   git push origin my-feature-branch
   ```

8. Wait for review and address any feedback

## Issues

We use GitHub issues to track public bugs or feature requests.

### Reporting Bugs

When reporting bugs, please include:
- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (Python version, OS, Hatchling version)
- Minimal reproducible example if possible
- Relevant logs or error messages

### Feature Requests

For feature requests, please include:
- A clear and concise description of the feature
- The motivation for the feature (what problem does it solve?)
- Examples of how the feature would be used
- Any alternatives you've considered

## Code Style

This project follows specific code style guidelines:

- **Formatting**: We use Black with a line length of 100
- **Linting**: We use Ruff for linting
- **Docstrings**: Google-style docstrings
- **Type hints**: We use type hints throughout the codebase
- **Imports**: Sorted using isort

Pre-commit hooks will automatically check and fix many style issues.

## Testing Guidelines

- Write tests for all new functionality
- Maintain or improve code coverage
- Unit tests should be fast and focused
- Integration tests should test end-to-end functionality
- Use descriptive test names that explain what is being tested
- Follow the existing test structure and patterns

## Documentation

Good documentation is crucial:

- Update docstrings for any changed functions/classes
- Add examples to docstrings when helpful
- Update README.md for user-facing changes
- Keep documentation up to date with code changes
- Use clear and concise language

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub Discussions
- Ask in an issue
- Reach out to the maintainers

We're here to help and appreciate your contributions!

## Code of Conduct

This project adheres to a [Code of Conduct](../CODE_OF_CONDUCT.md). By participating, you are 
expected to uphold this code.

## License

By contributing to `hatchling-autoextras-hook`, you agree that your contributions will be licensed
under the LICENSE file in the root directory of this source tree.
