#!/bin/bash
# Release script for publishing to PyPI
# Usage: ./release.sh

set -e  # Exit on error

echo "===================================="
echo "  Typer-GUI Release Script"
echo "===================================="
echo ""

# Clean previous builds
if [ -d "dist" ]; then
    echo "Cleaning previous builds..."
    rm -rf dist
    echo "Previous builds cleaned."
    echo ""
fi

# Build the package
echo "Building package..."
python -m build
echo "Build successful!"
echo ""

# Upload to PyPI
echo "Uploading to PyPI..."
echo "You will be prompted for credentials:"
echo "  Username: __token__"
echo "  Password: [Your PyPI API token]"
echo ""
python -m twine upload dist/*

echo ""
echo "===================================="
echo "  Release completed successfully!"
echo "===================================="
echo ""
echo "Your package is now available on PyPI."
echo "Check: https://pypi.org/project/typer-gui/"
