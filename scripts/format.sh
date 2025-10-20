#!/bin/bash
# Code formatting script
# This script automatically formats code using black and isort

set -e  # Exit on first error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories to format
DIRS="app/ agents/ tools/ infra/"

echo "=========================================="
echo "Running Code Formatters"
echo "=========================================="
echo ""

# Check if required tools are installed
echo "Checking for required tools..."
command -v black >/dev/null 2>&1 || { echo -e "${RED}Error: black is not installed. Run: pip install black${NC}" >&2; exit 1; }
command -v isort >/dev/null 2>&1 || { echo -e "${RED}Error: isort is not installed. Run: pip install isort${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ All required tools are installed${NC}"
echo ""

# Run black
echo "=========================================="
echo "1. Running black (code formatter)"
echo "=========================================="
black $DIRS
echo -e "${GREEN}✓ Black formatting complete${NC}"
echo ""

# Run isort
echo "=========================================="
echo "2. Running isort (import sorter)"
echo "=========================================="
isort $DIRS
echo -e "${GREEN}✓ Import sorting complete${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}Code formatting complete!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}Note: Run 'scripts/lint.sh' to check for any remaining issues${NC}"
