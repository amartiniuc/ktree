#!/usr/bin/env python3
"""
Build distributable binaries for ktree across multiple platforms.

This script uses PyInstaller to create standalone executables that can run
on Linux, macOS, and Windows without requiring Python to be installed.

Usage:
    python scripts/build_binaries.py [--platform PLATFORM] [--clean]

Platforms:
    - linux: Build for Linux (x86_64)
    - macos: Build for macOS (x86_64 and arm64)
    - windows: Build for Windows (x86_64)
    - all: Build for all platforms (requires running on each platform)
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# Platform identifiers
PLATFORMS = {
    "linux": {"name": "linux", "ext": "", "arch": ["x86_64"]},
    "macos": {"name": "macos", "ext": "", "arch": ["x86_64", "arm64"]},
    "windows": {"name": "windows", "ext": ".exe", "arch": ["x86_64"]},
}

# Current platform detection
CURRENT_PLATFORM = platform.system().lower()
if CURRENT_PLATFORM == "darwin":
    CURRENT_PLATFORM = "macos"


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def clean_build_artifacts():
    """Clean PyInstaller build artifacts."""
    project_root = get_project_root()
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"Cleaning {dir_path}...")
            shutil.rmtree(dir_path)
    
    # Clean .spec files
    for spec_file in project_root.glob("*.spec"):
        print(f"Removing {spec_file}...")
        spec_file.unlink()
    
    print("Clean complete!")


def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def create_pyinstaller_spec(project_root, platform_name, arch):
    """Create a PyInstaller spec file for the build."""
    main_py_path = (project_root / "ktree" / "main.py").as_posix()
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{main_py_path}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'kubernetes',
        'textual',
        'rich',
        'yaml',
        'urllib3',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ktree',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='{arch}',
    codesign_identity=None,
    entitlements_file=None,
)
"""
    spec_file = project_root / f"ktree_{platform_name}_{arch}.spec"
    spec_file.write_text(spec_content)
    return spec_file


def build_for_platform(platform_name, arch=None, clean=False):
    """Build binary for a specific platform."""
    project_root = get_project_root()
    
    if clean:
        clean_build_artifacts()
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Determine architecture
    if arch is None:
        if platform_name == "macos":
            # Default to current architecture on macOS
            machine = platform.machine().lower()
            if machine in ["arm64", "aarch64"]:
                arch = "arm64"
            else:
                arch = "x86_64"
        else:
            arch = "x86_64"
    
    print(f"\n{'='*60}")
    print(f"Building for {platform_name} ({arch})")
    print(f"{'='*60}\n")
    
    # Create spec file
    spec_file = create_pyinstaller_spec(project_root, platform_name, arch)
    
    try:
        # Build with PyInstaller
        cmd = [
            sys.executable,
            "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file),
        ]
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd, cwd=project_root)
        
        # Organize output
        dist_dir = project_root / "dist"
        platform_dist_dir = dist_dir / f"{platform_name}-{arch}"
        platform_dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Move executable to platform-specific directory
        exe_name = f"ktree{PLATFORMS[platform_name]['ext']}"
        exe_source = dist_dir / exe_name
        exe_dest = platform_dist_dir / exe_name
        
        if exe_source.exists():
            if exe_dest.exists():
                exe_dest.unlink()
            shutil.move(str(exe_source), str(exe_dest))
            print(f"\n✓ Binary created: {exe_dest}")
            print(f"  Size: {exe_dest.stat().st_size / (1024*1024):.2f} MB")
        else:
            print(f"\n✗ Error: Executable not found at {exe_source}")
            return False
        
        # Clean up spec file
        spec_file.unlink()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def build_all_platforms(clean=False):
    """Build binaries for all platforms (if possible)."""
    project_root = get_project_root()
    dist_dir = project_root / "dist"
    
    print("Building binaries for all platforms...")
    print(f"Current platform: {CURRENT_PLATFORM}\n")
    
    success_count = 0
    total_count = 0
    
    # Build for current platform
    if CURRENT_PLATFORM in PLATFORMS:
        platform_info = PLATFORMS[CURRENT_PLATFORM]
        for arch in platform_info["arch"]:
            total_count += 1
            if build_for_platform(CURRENT_PLATFORM, arch, clean=(clean and success_count == 0)):
                success_count += 1
            clean = False  # Only clean once
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Build Summary: {success_count}/{total_count} successful")
    print(f"{'='*60}\n")
    
    if dist_dir.exists():
        print("Built binaries:")
        for platform_dir in sorted(dist_dir.iterdir()):
            if platform_dir.is_dir():
                for exe in platform_dir.glob("ktree*"):
                    size_mb = exe.stat().st_size / (1024*1024)
                    print(f"  {platform_dir.name}/{exe.name} ({size_mb:.2f} MB)")
    
    print("\nNote: To build for other platforms, run this script on those platforms.")
    print("Alternatively, use Docker or CI/CD for cross-platform builds.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build distributable binaries for ktree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build for current platform
  python scripts/build_binaries.py

  # Build for specific platform (if supported)
  python scripts/build_binaries.py --platform macos

  # Build for all supported architectures on current platform
  python scripts/build_binaries.py --platform all

  # Clean and rebuild
  python scripts/build_binaries.py --clean
        """
    )
    
    parser.add_argument(
        "--platform",
        choices=["linux", "macos", "windows", "all"],
        default=None,
        help="Platform to build for (default: current platform)"
    )
    
    parser.add_argument(
        "--arch",
        choices=["x86_64", "arm64"],
        default=None,
        help="Architecture to build for (default: auto-detect)"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    os.chdir(project_root)
    
    # Determine platform
    if args.platform == "all":
        build_all_platforms(clean=args.clean)
    else:
        target_platform = args.platform or CURRENT_PLATFORM
        
        if target_platform not in PLATFORMS:
            print(f"Error: Platform '{target_platform}' is not supported.")
            print(f"Supported platforms: {', '.join(PLATFORMS.keys())}")
            sys.exit(1)
        
        if build_for_platform(target_platform, args.arch, clean=args.clean):
            print("\n✓ Build completed successfully!")
        else:
            print("\n✗ Build failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()

