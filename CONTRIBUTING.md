# Contributing to MC-Agent-Kit

Thank you for your interest in contributing to MC-Agent-Kit! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your changes
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.13+
- uv (package manager)

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/your-username/mc-agent-kit.git
cd mc-agent-kit

# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/your-feature-name` for new features
- `fix/issue-description` for bug fixes
- `docs/what-you-changed` for documentation updates

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Write docstrings for public functions and classes
- Keep line length under 100 characters

### Running Linters

```bash
# Check code style
uv run ruff check src/

# Auto-fix issues
uv run ruff check src/ --fix

# Type checking
uv run mypy src/
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest src/tests/test_launcher.py

# Run with verbose output
uv run pytest -v
```

### Writing Tests

- Place tests in `src/tests/`
- Name test files `test_*.py`
- Name test functions `test_*`
- All new code should have tests

### Test Coverage

We aim for high test coverage. Before submitting a PR:

1. Run tests to ensure they pass
2. Add tests for new functionality
3. Update tests if you change existing behavior

## Commit Messages

Follow these guidelines for commit messages:

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(launcher): add support for custom game paths

fix(knowledge): resolve issue with empty search results

docs(readme): update installation instructions
```

## Pull Requests

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Description

Include:
1. What changes you made
2. Why you made these changes
3. Any relevant issue numbers

### Review Process

1. A maintainer will review your PR
2. Address any feedback
3. Once approved, a maintainer will merge

## Project Structure

```
MC-Agent-Kit/
├── docs/                    # Documentation
│   ├── user/               # User documentation
│   └── *.md                # Project docs
├── examples/               # Example projects
├── skills/                 # OpenClaw Skills
├── src/
│   ├── mc_agent_kit/      # Main package
│   │   ├── launcher/      # Game launcher
│   │   ├── knowledge/     # Knowledge base
│   │   ├── generator/     # Code generation
│   │   ├── execution/     # Code execution
│   │   ├── completion/    # Code completion
│   │   ├── autofix/       # Auto-fix
│   │   ├── performance/   # Performance
│   │   └── skills/        # Agent skills
│   └── tests/             # Test files
├── pyproject.toml         # Project config
├── LICENSE                # MIT License
├── CHANGELOG.md           # Change log
└── CONTRIBUTING.md        # This file
```

## Questions?

Feel free to open an issue for questions or discussions.

Thank you for contributing!