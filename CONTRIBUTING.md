# Contributing to notion_client

Thank you for your interest in contributing to the notion_client package! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to learn and improve the codebase together.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/JobAutomation.git
   cd JobAutomation
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. **Install the package in development mode:**

   ```bash
   pip install -e ".[dev]"
   ```

2. **Verify installation:**
   ```bash
   python -c "from notion_client import NotionClient; print('Success!')"
   ```

### Development Dependencies

The `dev` extras include:

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `black` - Code formatter
- `ruff` - Fast Python linter
- `mypy` - Static type checker

## Making Changes

### Code Organization

```
notion_client/
├── __init__.py         # Package exports
├── client.py           # Main client implementation
├── config.py           # Configuration dataclass
├── exceptions.py       # Custom exceptions
├── helpers.py          # Helper functions
├── properties.py       # Property creators
└── tests/              # Test suite
    ├── conftest.py
    ├── test_client.py
    ├── test_config.py
    └── ...
```

### Guidelines

1. **Type Hints**: Always use type hints for function signatures

   ```python
   def create_page(self, page_id: str) -> Dict[str, Any]:
       ...
   ```

2. **Docstrings**: Use Google-style docstrings

   ```python
   def function_name(param1: str, param2: int) -> bool:
       """Brief description.

       More detailed description if needed.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Description of return value

       Raises:
           ValueError: When something is invalid
       """
   ```

3. **Error Handling**: Use custom exceptions from `exceptions.py`

   ```python
   raise NotionValidationError("Invalid property", status_code=400)
   ```

4. **Imports**: Group imports logically

   ```python
   # Standard library
   import logging
   from typing import Dict, Any

   # Third-party
   import requests

   # Local
   from .config import ClientConfig
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=notion_client

# Run specific test file
pytest notion_client/tests/test_client.py

# Run specific test
pytest notion_client/tests/test_client.py::TestNotionClient::test_init
```

### Writing Tests

1. **Place tests in `notion_client/tests/`**
2. **Name test files `test_*.py`**
3. **Use fixtures from `conftest.py`**
4. **Mock external API calls**

Example test:

```python
def test_get_page(client, sample_page_response):
    """Test get_page method."""
    with patch.object(client.session, 'request') as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = sample_page_response

        result = client.get_page("test-page-id")
        assert result["id"] == "test-page-id"
```

### Test Coverage

- Aim for **>80% code coverage**
- All new features must include tests
- Bug fixes should include regression tests

## Code Style

### Formatting

We use **Black** for code formatting:

```bash
# Format code
black notion_client/

# Check formatting
black --check notion_client/
```

### Linting

We use **Ruff** for linting:

```bash
# Lint code
ruff check notion_client/

# Auto-fix issues
ruff check --fix notion_client/
```

### Type Checking

We use **MyPy** for type checking:

```bash
mypy notion_client/ --exclude tests
```

### Pre-commit Checks

Before committing, run:

```bash
# Format
black notion_client/

# Lint
ruff check --fix notion_client/

# Test
pytest

# Type check
mypy notion_client/ --exclude tests
```

## Submitting Changes

### Commit Messages

Follow these guidelines:

- Use present tense ("Add feature" not "Added feature")
- First line: brief summary (50 chars or less)
- Blank line, then detailed description if needed
- Reference issues: "Fixes #123" or "Relates to #456"

Example:

```
Add multi-select property creator

Implement create_multi_select_property() function to support
multi-select properties in Notion databases.

Fixes #42
```

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Update CHANGELOG.md** with your changes
4. **Ensure CI passes** (all tests, linting, type checks)
5. **Submit PR** with clear description:

   ```markdown
   ## Description

   Brief description of changes

   ## Changes

   - Added X
   - Fixed Y
   - Updated Z

   ## Testing

   - [ ] Added tests
   - [ ] All tests pass
   - [ ] Documentation updated

   Fixes #issue_number
   ```

### PR Review

- Be patient and respectful
- Address review comments
- Update PR as needed
- Maintain clean commit history

## Reporting Bugs

### Before Submitting

1. **Check existing issues** to avoid duplicates
2. **Try latest version** of the package
3. **Gather information**:
   - Python version
   - notion_client version
   - Error messages and stack traces
   - Minimal reproduction code

### Bug Report Template

````markdown
**Describe the bug**
Clear description of what the bug is.

**To Reproduce**
Steps to reproduce:

1. Initialize client with...
2. Call method...
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Code sample**

```python
# Minimal reproduction code
```
````

**Environment**

- Python version:
- notion_client version:
- OS:

**Additional context**
Any other relevant information.

````

## Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Description of the problem.

**Describe the solution you'd like**
Clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**API examples**
```python
# How you'd like to use this feature
client.new_feature(...)
````

**Additional context**
Any other relevant information.

```

## Questions?

- **Documentation**: Check [README.md](notion_client/README.md)
- **Examples**: See [examples.ipynb](notion_client/examples.ipynb)
- **Issues**: Open an issue for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🎉
```
