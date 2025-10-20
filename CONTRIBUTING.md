# Contributing to SideKick

Thank you for your interest in contributing to SideKick! This document provides guidelines and instructions for contributing to the project.

## Code Quality Standards

We maintain high code quality standards using automated tools. All code must pass linting checks before being merged.

### Code Style

- **Python Version**: 3.11+
- **Style Guide**: PEP 8
- **Line Length**: 100 characters (configured in `.flake8`)
- **Formatter**: Black
- **Import Sorting**: isort

### Required Tools

Install development dependencies:

```bash
pip install -r scripts/requirements-dev.txt
```

This installs:
- `black` - Code formatter
- `isort` - Import sorter
- `flake8` - Linter

## Development Workflow

### 1. Before Starting Work

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Ensure you have the latest dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r scripts/requirements-dev.txt
   ```

### 2. During Development

Write clean, well-documented code:
- Add docstrings to all public functions and classes
- Use type hints where appropriate
- Write descriptive variable and function names
- Add comments for complex logic

### 3. Before Committing

**Always run these commands before committing:**

1. **Format your code:**
   ```bash
   ./scripts/format.sh
   ```

2. **Check for issues:**
   ```bash
   ./scripts/lint.sh
   ```

3. **Fix any remaining issues** that the linter reports

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```

### 4. Submitting a Pull Request

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub

3. Ensure CI checks pass (linting, tests, etc.)

4. Wait for code review

## CI/CD Pipeline

Our GitHub Actions workflow automatically runs linting checks on:
- All pushes to `main` and `develop` branches
- All pull requests to `main` and `develop` branches

**Your PR will not be merged if linting checks fail.**

## Code Quality Scripts

### Format Code (Auto-fix)
```bash
./scripts/format.sh
```
Automatically formats code using black and isort.

### Lint Code (Check Only)
```bash
./scripts/lint.sh
```
Checks code quality without modifying files. Used in CI/CD.

## Configuration Files

- **`.flake8`**: Flake8 linter configuration
- **`.github/workflows/lint.yml`**: GitHub Actions workflow for CI/CD
- **`scripts/requirements-dev.txt`**: Development dependencies

## IDE Setup

### VS Code

Recommended settings for VS Code (`.vscode/settings.json`):

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "python.sortImports.args": ["--profile", "black"]
}
```

### PyCharm

1. Install the Black plugin
2. Configure Black as the default formatter
3. Enable "Reformat code" on save
4. Configure isort integration

## Common Issues

### Linting fails locally but passes in CI (or vice versa)

- Ensure you're using Python 3.11
- Update dependencies: `pip install --upgrade -r scripts/requirements-dev.txt`
- Run `./scripts/format.sh` to auto-fix formatting

### Import order issues

Run `isort app/ agents/ tools/ infra/` to fix import sorting.

### Line too long errors

Break long lines into multiple lines or use parentheses for line continuation.

## Questions?

If you have questions about contributing, please:
1. Check the documentation in `docs/`
2. Review existing issues and PRs
3. Open a new issue with the `question` label

## License

By contributing to SideKick, you agree that your contributions will be licensed under the project's license.
