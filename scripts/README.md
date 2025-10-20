# Code Quality Scripts

This directory contains scripts for maintaining code quality in the SideKick project.

## Available Scripts

### 1. `lint.sh` - Linting Script (CI/CD)

Runs all code quality checks without modifying files. Perfect for CI/CD pipelines.

**Usage:**
```bash
./scripts/lint.sh
```

**What it checks:**
- **black**: Verifies code formatting (PEP 8 compliant)
- **isort**: Verifies import sorting
- **flake8**: Checks for style issues, unused variables, and other problems

**Exit codes:**
- `0`: All checks passed
- `1`: One or more checks failed

**CI/CD Integration:**
This script is designed to fail fast and provide clear error messages for CI/CD pipelines.

---

### 2. `format.sh` - Auto-formatting Script

Automatically formats code to fix style issues.

**Usage:**
```bash
./scripts/format.sh
```

**What it does:**
- Runs **black** to format all Python files
- Runs **isort** to sort imports

**Note:** Always run `lint.sh` after formatting to check for any remaining issues.

---

## Installation

### Install development dependencies:

```bash
pip install -r scripts/requirements-dev.txt
```

Or install individually:
```bash
pip install black isort flake8
```

---

## Configuration Files

The linting tools use the following configuration files in the project root:

- **`.flake8`**: Configuration for flake8 linter
  - Max line length: 100 characters
  - Ignores: E203, W503, E402
  - Excludes: `__pycache__`, `.venv`, `.git`, etc.

- **`pyproject.toml`** (optional): Can be used for black and isort configuration

---

## GitHub Actions Integration

A GitHub Actions workflow is provided at `.github/workflows/lint.yml` that:
- Runs on push and pull requests to `main` and `develop` branches
- Sets up Python 3.11
- Caches pip dependencies for faster builds
- Runs the linting script

---

## Local Development Workflow

### Before committing:

1. **Format your code:**
   ```bash
   ./scripts/format.sh
   ```

2. **Check for issues:**
   ```bash
   ./scripts/lint.sh
   ```

3. **Fix any remaining issues manually**

4. **Commit your changes**

### Pre-commit Hook (Optional)

You can set up a pre-commit hook to automatically run linting:

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
./scripts/lint.sh
EOF

chmod +x .git/hooks/pre-commit
```

---

## Troubleshooting

### "Command not found" errors

Make sure you've installed the development dependencies:
```bash
pip install -r scripts/requirements-dev.txt
```

### Scripts not executable

Make the scripts executable:
```bash
chmod +x scripts/lint.sh scripts/format.sh
```

### Linting fails in CI but passes locally

Make sure you're using the same Python version as CI (3.11) and have the latest dependencies:
```bash
pip install --upgrade -r scripts/requirements-dev.txt
```

---

## Additional Tools (Optional)

Consider adding these tools for even better code quality:

- **pylint**: More comprehensive linting
- **mypy**: Static type checking
- **bandit**: Security issue detection
- **pytest**: Unit testing

Install with:
```bash
pip install pylint mypy bandit pytest
```

---

## Questions?

For questions or issues with the linting scripts, please open an issue in the project repository.
