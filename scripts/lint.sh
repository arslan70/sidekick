#!/bin/bash
# Linting script for CI/CD pipeline
# This script runs code formatters and linters to ensure code quality

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories to lint
DIRS="app/ agents/ tools/ infra/"

echo "=========================================="
echo "Running Code Quality Checks"
echo "=========================================="
echo ""

# Check if required tools are installed
echo "Checking for required tools..."
command -v black >/dev/null 2>&1 || { echo -e "${RED}Error: black is not installed. Run: pip install black${NC}" >&2; exit 1; }
command -v isort >/dev/null 2>&1 || { echo -e "${RED}Error: isort is not installed. Run: pip install isort${NC}" >&2; exit 1; }
command -v flake8 >/dev/null 2>&1 || { echo -e "${RED}Error: flake8 is not installed. Run: pip install flake8${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ All required tools are installed${NC}"
echo ""

# Run black (code formatter)
echo "=========================================="
echo "1. Running black (code formatter)"
echo "=========================================="
if black --check $DIRS; then
    echo -e "${GREEN}✓ Black: All files are properly formatted${NC}"
else
    echo -e "${YELLOW}⚠ Black: Some files need formatting${NC}"
    echo "Run 'black $DIRS' to fix formatting issues"
    exit 1
fi
echo ""

# Run isort (import sorter)
echo "=========================================="
echo "2. Running isort (import sorter)"
echo "=========================================="
if isort --check-only $DIRS; then
    echo -e "${GREEN}✓ isort: All imports are properly sorted${NC}"
else
    echo -e "${YELLOW}⚠ isort: Some imports need sorting${NC}"
    echo "Run 'isort $DIRS' to fix import sorting"
    exit 1
fi
echo ""

# Run flake8 (linter)
echo "=========================================="
echo "3. Running flake8 (linter)"
echo "=========================================="
if flake8 $DIRS --count --statistics; then
    echo -e "${GREEN}✓ flake8: No linting issues found${NC}"
else
    echo -e "${RED}✗ flake8: Linting issues found${NC}"
    echo "Review the issues above and fix them"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}All code quality checks passed!${NC}"
echo "=========================================="
