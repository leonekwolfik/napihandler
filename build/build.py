#!/usr/bin/env python3
"""
build.py — buduje napihandler do standalone binarki przy użyciu PyInstaller.
Wynikowa binarka trafia do dist/napihandler.

Użycie:
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


def sprawdz_wymagania():
    if not shutil.which("pyinstaller"):
        print("Error: PyInstaller is not installed.")
        print("  Install: pip3 install pyinstaller")
        sys.exit(1)
    if not SRC.exists():
        print(f"Error: {SRC} not found")
        sys.exit(1)


def buduj():
    cmd = [
        "pyinstaller",
        "--name",
        "napihandler",  # nazwa pliku wynikowego
        "--distpath",
        str(DIST),  # gdzie trafia binarka
        "--workpath",
        str(BUILD_TMP),  # pliki tymczasowe
        "--specpath",
        str(BUILD_TMP),  # plik .spec
    ]

    # Różne opcje w zależności od platformy
    if sys.platform.startswith("win"):
        cmd.extend([
            "--onefile",  # jedna binarka na Windowsie
            "--runtime-tmpdir", "%TEMP%",  # użyj katalogu TEMP
        ])
    else:
        cmd.extend([
            "--onefile",  # jedna binarka na innych platformach
            "--strip",  # mniejszy rozmiar
        ])

    cmd.append(str(SRC))

    print(f"Building binary from {SRC} ...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\nError: Build failed.")
        sys.exit(1)


def posprzataj():
    if BUILD_TMP.exists():
        shutil.rmtree(BUILD_TMP)
    print("OK: Cleaned up temporary files")


def main():
    sprawdz_wymagania()
    buduj()
    posprzataj()

    binarka = DIST / "napihandler"
    print(f"\nOK: Done! Binary: {binarka}")
    print(f"\nTo install globally:")
    print(f"  sudo cp {binarka} /usr/local/bin/napihandler")


if __name__ == "__main__":
    main()
