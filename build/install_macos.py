#!/usr/bin/env python3
"""
install_macos.py — rejestruje napihandler jako handler protokołu napiprojekt: na macOS
Tworzy aplikację .app z odpowiednim Info.plist i rejestruje ją w systemie.
"""

import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent.resolve()
HANDLER_SCRIPT = SCRIPT_DIR / "src" / "napihandler.py"

APP_NAME = "NapiHandler"
APP_PATH = Path.home() / "Applications" / f"{APP_NAME}.app"

INFO_PLIST = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>pl.napiprojekt.napihandler</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>napihandler-app</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>LSUIElement</key>
    <true/>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>NapiProjekt Subtitles</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>napiprojekt</string>
            </array>
        </dict>
    </dict>
    </array>
</dict>
</plist>
"""

LAUNCHER_SH = f"""#!/bin/bash
# Launcher wywoływany przez macOS przy kliknięciu w link napiprojekt:
# Argument przekazywany przez macOS to URI, np. napiprojekt://HASH lub napiprojekt:HASH

URI="$1"

# Normalizuj URI (macOS może dodać //)
URI=$(echo "$URI" | sed 's|napiprojekt://|napiprojekt:|')

python3 "{HANDLER_SCRIPT}" "$URI"
"""


def stworz_app():
    contents = APP_PATH / "Contents"
    macos_dir = contents / "MacOS"
    resources_dir = contents / "Resources"

    for d in [macos_dir, resources_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Info.plist
    (contents / "Info.plist").write_text(INFO_PLIST)

    # Skrypt launcher
    launcher = macos_dir / "napihandler-app"
    launcher.write_text(LAUNCHER_SH)
    launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    print(f"✓ Utworzono aplikację: {APP_PATH}")


def zarejestruj():
    """Odśwież bazę handlerów protokołów macOS."""
    subprocess.run(
        ["/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/"
         "LaunchServices.framework/Versions/A/Support/lsregister",
         "-f", str(APP_PATH)],
        check=True,
    )
    print("✓ Zarejestrowano protokół napiprojekt: w systemie")
    print("  (może być konieczne wylogowanie/zalogowanie lub restart Findera)")


def sprawdz_wymagania():
    if sys.platform != "darwin":
        print("Błąd: Ten skrypt działa tylko na macOS")
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
    print(f"Instalacja NapiHandler dla macOS...")
    stworz_app()
    zarejestruj()
    print(f"\n✓ Gotowe! Kliknięcie w link napiprojekt: będzie otwierać napihandler.")
    print(f"  Napisy będą zapisywane w katalogu: {SCRIPT_DIR}")