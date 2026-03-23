#!/usr/bin/env python3
"""
build.py — builds napihandler into a standalone binary using PyInstaller.
The resulting binary goes to dist/napihandler.

Usage:
    python3 build/build.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Ustaw kodowanie UTF-8 dla Windows
if sys.platform.startswith("win"):
    import locale
    if locale.getpreferredencoding() != "utf-8":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).parent.parent.resolve()
SRC = ROOT / "src" / "napihandler.py"
DIST = ROOT / "dist"
BUILD_TMP = ROOT / "build" / "_tmp"


def check_requirements():
    if not shutil.which("pyinstaller"):
        print("Error: PyInstaller is not installed.")
        print("  Install: pip3 install pyinstaller")
        sys.exit(1)
    if not SRC.exists():
        print(f"Error: {SRC} not found")
        sys.exit(1)


def build():
    cmd = [
        "pyinstaller",
        "--name",
        "napihandler",  # output filename
        "--distpath",
        str(DIST),  # where the binary goes
        "--workpath",
        str(BUILD_TMP),  # temporary files
        "--specpath",
        str(BUILD_TMP),  # .spec file
    ]

    # Different options depending on platform
    if sys.platform.startswith("win"):
        cmd.extend([
            "--onefile",  # single binary on Windows
            "--runtime-tmpdir", "%TEMP%",  # use TEMP directory
        ])
    else:
        cmd.extend([
            "--onefile",  # single binary on other platforms
            "--strip",  # smaller size
        ])

    cmd.append(str(SRC))

    print(f"Building binary from {SRC} ...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\nError: Build failed.")
        sys.exit(1)


def cleanup():
    if BUILD_TMP.exists():
        shutil.rmtree(BUILD_TMP)
    print("OK: Cleaned up temporary files")


def main():
    check_requirements()
    build()
    cleanup()

    binary = DIST / "napihandler"
    print(f"\nOK: Done! Binary: {binary}")
    print(f"\nTo install globally:")
    print(f"  sudo cp {binary} /usr/local/bin/napihandler")


if __name__ == "__main__":
    main()
