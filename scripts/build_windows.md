# Building Windows Binaries

To build Windows binaries, you need to run the build script on a Windows machine.

## Requirements

- Windows 10 or later
- Python 3.10 or higher
- All project dependencies

## Steps

1. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Clone or copy the project** to your Windows machine

3. **Create a virtual environment**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

5. **Run the build script**
   ```cmd
   python scripts\build_binaries.py --platform windows
   ```

6. **Find your binary**
   The executable will be in `dist\windows-x86_64\ktree.exe`

## Alternative: Using WSL (Windows Subsystem for Linux)

If you have WSL installed, you can build Linux binaries from Windows:

```bash
# In WSL
cd /mnt/c/path/to/ktree
source venv/bin/activate
python scripts/build_binaries.py --platform linux
```

## Using CI/CD

For automated builds, consider using:
- **GitHub Actions** - Can build for Linux, macOS, and Windows
- **GitLab CI** - Multi-platform support
- **Azure Pipelines** - Windows and Linux agents
- **CircleCI** - Multi-platform support

See the `.github/workflows` directory for example CI/CD configurations.

