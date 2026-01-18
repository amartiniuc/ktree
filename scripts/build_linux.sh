#!/bin/bash
# Build Linux binary using Docker
# This allows building Linux binaries from any platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Building Linux binary using Docker..."
echo "This will create a Docker container with Python and build the binary"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    echo "Please install Docker to build Linux binaries"
    exit 1
fi

# Build using Docker
docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /workspace \
    python:3.10 \
    bash -c "
        echo 'Installing dependencies...'
        pip install --quiet pyinstaller kubernetes textual rich
        
        echo 'Building Linux binary...'
        python scripts/build_binaries.py --platform linux
        
        echo ''
        echo 'Build complete! Binary is in dist/linux-x86_64/'
    "

echo ""
echo "✓ Linux binary build complete!"
echo "Binary location: dist/linux-x86_64/ktree"

