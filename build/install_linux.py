#!/usr/bin/env python3
"""
install_linux.py — rejestruje napihandler jako handler protokołu napiprojekt: na Linux
Tworzy plik .desktop i rejestruje go przez xdg-mime (działa z GNOME, KDE, XFCE, itp.)
"""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent.resolve()
HANDLER_SCRIPT = SCRIPT_DIR / "src" / "napihandler.py"

DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"
DESKTOP_FILE = DESKTOP_DIR / "napihandler.desktop"
BIN_DIR = Path.home() / ".local" / "bin"
BIN_FILE = BIN_DIR / "napihandler"

DESKTOP_ENTRY = f"""[Desktop Entry]
Name=NapiHandler
Comment=Pobiera napisy z NapiProjekt
Exec=python3 {HANDLER_SCRIPT} %u
Type=Application
NoDisplay=true
MimeType=x-scheme-handler/napiprojekt;
"""

WRAPPER_SH = f"""#!/bin/bash
# Wrapper wywoływany przez xdg-open przy kliknięciu w link napiprojekt:
python3 "{HANDLER_SCRIPT}" "$@"
"""


def stworz_desktop_entry():
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_FILE.write_text(DESKTOP_ENTRY)
    print(f"✓ Utworzono plik .desktop: {DESKTOP_FILE}")


def stworz_wrapper():
    """Opcjonalny wrapper w ~/.local/bin dla użycia z CLI."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    BIN_FILE.write_text(WRAPPER_SH)
    BIN_FILE.chmod(BIN_FILE.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"✓ Utworzono skrypt CLI: {BIN_FILE}")


def zarejestruj():
    """Zarejestruj handler protokołu przez xdg-mime."""
    if not shutil.which("xdg-mime"):
        print("Ostrzeżenie: Nie znaleziono xdg-mime — rejestracja ręczna")
        print(f"  Uruchom: xdg-mime default napihandler.desktop x-scheme-handler/napiprojekt")
        return

    subprocess.run(
        ["xdg-mime", "default", "napihandler.desktop", "x-scheme-handler/napiprojekt"],
        check=True,
    )
    print("✓ Zarejestrowano protokół napiprojekt: przez xdg-mime")

    # Odśwież bazę MIME (dla środowisk opartych na GTK)
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], check=True)
        print("✓ Odświeżono bazę desktop entries")


def sprawdz_path():
    """Sprawdź czy ~/.local/bin jest w PATH."""
    path_dirs = os.environ.get("PATH", "").split(":")
    if str(BIN_DIR) not in path_dirs:
        print(f"\n⚠ Dodaj do swojego ~/.bashrc lub ~/.zshrc:")
        print(f'  export PATH="$HOME/.local/bin:$PATH"')


def sprawdz_wymagania():
    if sys.platform == "darwin":
        print("Błąd: Na macOS użyj install_macos.py")
        sys.exit(1)
    if not HANDLER_SCRIPT.exists():
        print(f"Błąd: Nie znaleziono napihandler.py w {SCRIPT_DIR}")
        sys.exit(1)
    try:
        import requests  # noqa
    except ImportError:
        print("Błąd: Brak biblioteki 'requests'. Zainstaluj: pip3 install requests")
        sys.exit(1)


if __name__ == "__main__":
    sprawdz_wymagania()
    print("Instalacja NapiHandler dla Linux...")
    stworz_desktop_entry()
    stworz_wrapper()
    zarejestruj()
    sprawdz_path()
    print(f"\n✓ Gotowe! Kliknięcie w link napiprojekt: będzie otwierać napihandler.")
    print(f"  Napisy będą zapisywane w bieżącym katalogu.")
