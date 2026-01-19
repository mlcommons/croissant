#!/bin/bash
set -e

echo "🏗️  Building Eclair package..."

# Clean up any previous builds
rm -rf build/ dist/ src/eclair.egg-info/

# Install build dependencies
pip install build twine

# Build the package
python -m build

echo "✅ Package built successfully!"
echo "📦 Files created:"
ls -la dist/

echo ""
echo "To install locally: pip install dist/eclair-0.0.1-py3-none-any.whl"
echo "To install in development mode: pip install -e ."
