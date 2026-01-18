# Contributing to KTree

Thank you for your interest in contributing to KTree! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/ktree.git
   cd ktree
   ```
3. **Set up development environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

## Development Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** and test them:
   ```bash
   # Run tests
   pytest
   
   # Run linting
   ruff check .
   
   # Format code
   black .
   ```

3. **Commit your changes** with clear commit messages:
   ```bash
   git add .
   git commit -m "Add feature: description of what you did"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

## Code Style

- Follow PEP 8 style guidelines
- Use `black` for code formatting
- Use `ruff` for linting
- Maximum line length: 100 characters
- Use type hints where appropriate

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ktree

# Run specific test file
pytest tests/test_app_functional.py
```

## Project Structure

- `ktree/` - Main application code
- `tests/` - Test files
- `scripts/` - Build and utility scripts
- `images/` - Screenshots and images for documentation

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Update documentation if needed
- Add tests for new features
- Ensure all tests pass
- Update CHANGELOG.md if applicable

## Reporting Issues

When reporting issues, please include:
- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant error messages or logs

## Feature Requests

For feature requests, please:
- Check if the feature already exists or is planned
- Describe the use case
- Explain how it would benefit users
- Consider implementation complexity

## Questions?

Feel free to open an issue for questions or discussions about the project.

Thank you for contributing to KTree! 🎉

