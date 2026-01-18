# Building Distributable Binaries

This directory contains scripts to build standalone executables for ktree that can run on any platform without requiring Python to be installed.

## Quick Start

```bash
# Build for current platform
python scripts/build_binaries.py

# Or use the shell script
./scripts/build_binaries.py
```

## Output

Binaries are placed in the `dist/` directory, organized by platform and architecture:

```
dist/
├── linux-x86_64/
│   └── ktree
├── macos-x86_64/
│   └── ktree
├── macos-arm64/
│   └── ktree
└── windows-x86_64/
    └── ktree.exe
```

## Usage

### Build for Current Platform

```bash
python scripts/build_binaries.py
```

### Build for Specific Platform

```bash
# Linux
python scripts/build_binaries.py --platform linux

# macOS
python scripts/build_binaries.py --platform macos

# Windows
python scripts/build_binaries.py --platform windows
```

### Build for Specific Architecture

```bash
# macOS ARM64 (Apple Silicon)
python scripts/build_binaries.py --platform macos --arch arm64

# macOS x86_64 (Intel)
python scripts/build_binaries.py --platform macos --arch x86_64
```

### Clean Build

```bash
# Clean previous builds and rebuild
python scripts/build_binaries.py --clean
```

## Cross-Platform Building

To build binaries for all platforms, you need to run the script on each platform:

1. **Linux**: Run on a Linux machine or Docker container
2. **macOS**: Run on a macOS machine (supports both x86_64 and arm64)
3. **Windows**: Run on a Windows machine

### Using Docker for Cross-Platform Builds

You can use Docker to build for Linux from any platform:

```bash
# Build Linux binary using Docker
docker run --rm -v "$(pwd):/workspace" -w /workspace python:3.10 \
  bash -c "pip install pyinstaller && python scripts/build_binaries.py --platform linux"
```

## Requirements

- Python 3.10 or higher
- PyInstaller (installed automatically by the script)
- All project dependencies (from requirements.txt)

## Notes

- The binaries are standalone and include all dependencies
- Binary size is typically 30-50 MB depending on platform
- The binaries require access to a Kubernetes cluster via kubeconfig
- All command-line arguments work the same as the Python version

## Troubleshooting

### "PyInstaller not found"
The script will automatically install PyInstaller, but if it fails, install manually:
```bash
pip install pyinstaller
```

### Large binary size
This is normal - PyInstaller bundles Python and all dependencies. The binary is self-contained and doesn't require Python to be installed.

### Binary doesn't run
- Ensure the binary has execute permissions: `chmod +x dist/linux-x86_64/ktree`
- Check that you have the correct architecture for your system
- Verify kubeconfig access on the target system

