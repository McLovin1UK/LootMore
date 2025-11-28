"""Build a Windows installer for Lootmore using PyInstaller + NSIS.

This script is intended for CI on Windows runners but can also be used
locally to verify builds. PyInstaller creates a one-file executable, and
NSIS wraps it into a simple installer (LootmoreSetup.exe).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
NSIS_TEMPLATE = ROOT / "installer" / "lootmore_installer.nsi"
VERSION_FILE = ROOT / "VERSION"


def read_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


def run(cmd: List[str]) -> None:
    print(f"[build] running: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def build_pyinstaller(version: str) -> Path:
    os.makedirs(DIST, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)

    sep = os.pathsep
    base_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(ROOT / "lootmore_launcher.py"),
        "--onefile",
        "--noconfirm",
        "--name",
        "Lootmore",
        "--noconsole",
        f"--add-data={ROOT / 'ai_guide_arc_raiders.py'}{sep}.",
        f"--add-data={ROOT / 'guide_hotkey.py'}{sep}.",
        f"--add-data={ROOT / 'config.py'}{sep}.",
        f"--add-data={ROOT / 'client'}{sep}client",
        f"--add-data={ROOT / 'lootmore_launcher.py'}{sep}.",
        f"--add-data={ROOT / 'VERSION'}{sep}.",
        "--hidden-import",
        "client.logging_setup",
        "--hidden-import",
        "client.onboarding",
    ]

    run(base_cmd)
    exe_path = ROOT / "dist" / "Lootmore.exe"
    if not exe_path.exists():
        raise FileNotFoundError("PyInstaller output missing: Lootmore.exe")
    return exe_path


def render_nsis(version: str) -> Path:
    target_script = BUILD / "lootmore_installer.generated.nsi"
    template = NSIS_TEMPLATE.read_text(encoding="utf-8")
    rendered = template.replace("@VERSION@", version)
    target_script.write_text(rendered, encoding="utf-8")
    return target_script


def build_nsis(installer_script: Path) -> Path:
    output = DIST / "LootmoreSetup.exe"
    cmd = ["makensis", f"/DOUTPUT={output}", str(installer_script)]
    run(cmd)
    if not output.exists():
        raise FileNotFoundError("NSIS output missing: LootmoreSetup.exe")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-nsis", action="store_true", help="Only run PyInstaller")
    args = parser.parse_args()

    version = read_version()
    print(f"[build] Lootmore version {version}")

    exe_path = build_pyinstaller(version)
    print(f"[build] PyInstaller output: {exe_path}")

    if args.skip_nsis:
        return

    installer_script = render_nsis(version)
    installer = build_nsis(installer_script)
    print(f"[build] Created installer: {installer}")


if __name__ == "__main__":
    main()
