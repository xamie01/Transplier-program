# Contributing to Transplier

Thank you for your interest in contributing to Transplier! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

Please be respectful and constructive in all interactions with the project community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Transplier-program.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Describe the bug in detail
- Include steps to reproduce
- Provide example code if possible

### Suggesting Features

- Open an issue with the "enhancement" label
- Clearly describe the feature and its use case
- Discuss the implementation approach

### Adding Support for New Languages

To add support for a new trading language:

1. **Create a Parser** in `src/parsers/`:
   - Inherit from `BaseParser`
   - Implement `parse()`, `extract_indicators()`, and `extract_conditions()`
   - Add pattern matching for language-specific syntax

2. **Create a Generator** in `src/generators/`:
   - Inherit from `BaseGenerator`
   - Implement `generate()`, `generate_indicators()`, and `generate_conditions()`
   - Generate valid code for the target language

3. **Add Tests**:
   - Create test files in `tests/`
   - Test parsing and generation
   - Test round-trip conversion if possible

4. **Update Documentation**:
   - Add examples in `examples/`
   - Update README with supported language

## Coding Standards

### Python Style Guide

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and concise

### Code Formatting

We use `black` for code formatting:

```bash
black src/ tests/
```

### Linting

We use `flake8` for linting:

```bash
flake8 src/ tests/
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_transpiler.py
```

### Writing Tests

- Write tests for all new features
- Aim for high code coverage
- Use descriptive test names
- Follow the existing test structure

## Submitting Changes

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**:
   - Provide a clear title and description
   - Reference any related issues
   - Ensure all tests pass
   - Request review from maintainers

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added for new features
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive

## Project Structure

```
Transplier-program/
├── src/
│   ├── ir/              # Intermediate representation
│   ├── parsers/         # Language parsers
│   ├── generators/      # Code generators
│   ├── indicators/      # Technical indicators
│   ├── position/        # Position sizing
│   ├── conditions/      # Trading conditions
│   ├── utils/           # Utility functions
│   ├── transpiler.py    # Main transpiler class
│   └── converter.py     # High-level converter API
├── tests/               # Test files
├── examples/            # Example strategies
└── docs/                # Documentation

```

## Questions?

If you have questions, please:
- Open an issue for discussion
- Check existing issues and documentation
- Reach out to maintainers

Thank you for contributing to Transplier!
