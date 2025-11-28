# Packaging Lootmore for Local Testing (Windows EXE)

The repo already includes a build script and NSIS template to produce a one-file EXE and optional Windows installer. Follow these steps on a Windows machine to package the current code for local testing.

## Prerequisites
- Windows 10/11
- Python 3.10+ available in `PATH`
- `pip install --upgrade pip`
- Build tools: `pip install pyinstaller` (CLI: `pyinstaller`)
- Optional installer wrapping: [NSIS](https://nsis.sourceforge.io/Download) installed and `makensis` available in `PATH` (e.g., `choco install nsis`)

## Quick one-file EXE (no installer)
1. Clone or pull the repository.
2. From the repo root, run:
   ```powershell
   python scripts/build_installer.py --skip-nsis
   ```
3. The single-file executable will be written to `dist/Lootmore.exe`. Double-click to launch.

## Full installer build (LootmoreSetup.exe)
1. Ensure NSIS is installed and `makensis` is in `PATH`.
2. Run the full build:
   ```powershell
   python scripts/build_installer.py
   ```
3. Outputs:
   - `dist/Lootmore.exe` (PyInstaller one-file build)
   - `dist/LootmoreSetup.exe` (NSIS installer wrapping the one-file build)

## Notes
- Version metadata comes from the `VERSION` file and is injected into the generated NSIS script.
- Build artifacts are written to `dist/`; intermediate files go to `build/`.
- If PyInstaller or NSIS are missing, the script will raise an error—install the prerequisites above and rerun.
- The GitHub Actions workflow `.github/workflows/build-release.yml` runs the same script on tagged releases.
