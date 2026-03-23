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

ROOT = Path(__file__).parent.parent.resolve()
SRC = ROOT / "src" / "napihandler.py"
DIST = ROOT / "dist"
BUILD_TMP = ROOT / "build" / "_tmp"


def sprawdz_wymagania():
    if not shutil.which("pyinstaller"):
        print("Błąd: PyInstaller nie jest zainstalowany.")
        print("  Zainstaluj: pip3 install pyinstaller")
        sys.exit(1)
    if not SRC.exists():
        print(f"Błąd: Nie znaleziono {SRC}")
        sys.exit(1)


def buduj():
    cmd = [
        "pyinstaller",
        "--onefile",  # jedna binarka
        "--name",
        "napihandler",  # nazwa pliku wynikowego
        "--distpath",
        str(DIST),  # gdzie trafia binarka
        "--workpath",
        str(BUILD_TMP),  # pliki tymczasowe
        "--specpath",
        str(BUILD_TMP),  # plik .spec
        "--strip",  # mniejszy rozmiar
        str(SRC),
    ]

    print(f"Budowanie binarki z {SRC} ...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\nBłąd: Budowanie nie powiodło się.")
        sys.exit(1)


def posprzataj():
    if BUILD_TMP.exists():
        shutil.rmtree(BUILD_TMP)
    print("✓ Usunięto pliki tymczasowe")


def main():
    sprawdz_wymagania()
    buduj()
    posprzataj()

    binarka = DIST / "napihandler"
    print(f"\n✓ Gotowe! Binarka: {binarka}")
    print(f"\nAby zainstalować globalnie:")
    print(f"  sudo cp {binarka} /usr/local/bin/napihandler")


if __name__ == "__main__":
    main()
