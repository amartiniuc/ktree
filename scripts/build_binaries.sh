#!/bin/bash
# Build distributable binaries for ktree across multiple platforms
# This is a wrapper script that calls the Python build script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the Python build script
python3 "$SCRIPT_DIR/build_binaries.py" "$@"

