# Cross-Platform Binary Building Guide

This document explains how to build binaries for all supported platforms.

## Current Status

### ✅ Built Successfully
- **macOS ARM64** (Apple Silicon) - Built natively
- **Linux x86_64** - Built using Docker

### ⚠️ Requires Different Environment
- **macOS x86_64** (Intel) - Cannot cross-compile from ARM64 Mac
- **Windows x86_64** - Requires Windows machine or CI/CD

## Platform-Specific Build Instructions

### macOS

#### ARM64 (Apple Silicon) - ✅ Works
```bash
source venv/bin/activate
python scripts/build_binaries.py --platform macos --arch arm64
```

#### x86_64 (Intel) - ⚠️ Requires Intel Mac
Cross-compilation from ARM64 to x86_64 is not supported by PyInstaller.
You need to run on an Intel Mac:
```bash
source venv/bin/activate
python scripts/build_binaries.py --platform macos --arch x86_64
```

### Linux

#### x86_64 - ✅ Works via Docker
```bash
./scripts/build_linux.sh
```

Or manually:
```bash
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    python:3.10 \
    bash -c "pip install pyinstaller kubernetes textual rich && python scripts/build_binaries.py --platform linux"
```

### Windows

#### x86_64 - ⚠️ Requires Windows Machine
See [build_windows.md](build_windows.md) for detailed instructions.

Quick steps:
1. Install Python 3.10+ on Windows
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Build: `python scripts\build_binaries.py --platform windows`

## Using CI/CD for All Platforms

The best way to build for all platforms is using CI/CD. Here are some options:

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Build Binaries

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build binary
        run: |
          if [ "${{ matrix.os }}" == "ubuntu-latest" ]; then
            python scripts/build_binaries.py --platform linux
          elif [ "${{ matrix.os }}" == "macos-latest" ]; then
            python scripts/build_binaries.py --platform macos --arch arm64
          else
            python scripts/build_binaries.py --platform windows
          fi
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ktree-${{ matrix.os }}
          path: dist/
```

## Summary

| Platform | Architecture | Status | Method |
|----------|-------------|--------|--------|
| macOS | ARM64 | ✅ Built | Native |
| macOS | x86_64 | ⚠️ Needs Intel Mac | Native only |
| Linux | x86_64 | ✅ Built | Docker |
| Windows | x86_64 | ⚠️ Needs Windows | Native or CI/CD |

## Distribution

After building, your `dist/` folder will contain:

```
dist/
├── macos-arm64/
│   └── ktree          (17.45 MB)
├── macos-x86_64/      (requires Intel Mac)
│   └── ktree
├── linux-x86_64/
│   └── ktree          (22.71 MB)
└── windows-x86_64/    (requires Windows)
    └── ktree.exe
```

## Notes

- Binaries are standalone and don't require Python
- Binary sizes are typically 15-25 MB
- All binaries require access to a Kubernetes cluster via kubeconfig
- Test binaries on target platforms before distribution

