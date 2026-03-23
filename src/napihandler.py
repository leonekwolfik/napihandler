#!/usr/bin/env python3
"""
napihandler — pobiera napisy z NapiProjekt przez protokół napiprojekt:

Użycie:
    napihandler --register                          # jednorazowa rejestracja protokołu
    napihandler "napiprojekt:HASH"                  # pobieranie napisów
    napihandler "napiprojekt:HASH" --jezyk EN       # inny język
    napihandler "napiprojekt:HASH" -o film.srt      # własna nazwa pliku
"""

import argparse
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Rejestracja protokołu
# ---------------------------------------------------------------------------

def binary_path() -> Path:
    """Ścieżka do aktualnie uruchomionej binarki (lub skryptu)."""
    return Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()


def zarejestruj_macos():
    exe = binary_path()
    app_dir = Path.home() / "Applications" / "NapiHandler.app"
    macos_dir = app_dir / "Contents" / "MacOS"
    macos_dir.mkdir(parents=True, exist_ok=True)

    # Info.plist — rejestruje schemat napiprojekt:
    plist = app_dir / "Contents" / "Info.plist"
    plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>NapiHandler</string>
    <key>CFBundleIdentifier</key><string>pl.napiprojekt.napihandler</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundleExecutable</key><string>napihandler-launcher</string>
    <key>LSMinimumSystemVersion</key><string>10.13</string>
    <key>LSUIElement</key><true/>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key><string>NapiProjekt Subtitles</string>
            <key>CFBundleURLSchemes</key>
            <array><string>napiprojekt</string></array>
        </dict>
    </array>
</dict>
</plist>
""")

    # Launcher — macOS przekazuje URI jako argument
    launcher = macos_dir / "napihandler-launcher"
    launcher.write_text(f"""#!/bin/bash
URI=$(echo "$1" | sed 's|napiprojekt://|napiprojekt:|')
"{exe}" "$URI"
""")
    launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Zarejestruj .app w LaunchServices
    lsregister = (
        "/System/Library/Frameworks/CoreServices.framework/Versions/A"
        "/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
    )
    subprocess.run([lsregister, "-f", str(app_dir)], check=True)

    print(f"✓ Utworzono: {app_dir}")
    print("✓ Zarejestrowano protokół napiprojekt: w systemie")
    print("  Może być konieczne wylogowanie lub restart Findera.")


def zarejestruj_linux():
    exe = binary_path()
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    desktop_file = desktop_dir / "napihandler.desktop"
    desktop_file.write_text(f"""[Desktop Entry]
Name=NapiHandler
Comment=Pobiera napisy z NapiProjekt
Exec="{exe}" %u
Type=Application
NoDisplay=true
MimeType=x-scheme-handler/napiprojekt;
""")
    print(f"✓ Utworzono: {desktop_file}")

    if shutil.which("xdg-mime"):
        subprocess.run(
            ["xdg-mime", "default", "napihandler.desktop", "x-scheme-handler/napiprojekt"],
            check=True,
        )
        print("✓ Zarejestrowano protokół napiprojekt: przez xdg-mime")
    else:
        print("⚠ Nie znaleziono xdg-mime — uruchom ręcznie:")
        print("  xdg-mime default napihandler.desktop x-scheme-handler/napiprojekt")

    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(desktop_dir)], check=True)
        print("✓ Odświeżono bazę desktop entries")


def zarejestruj():
    print("Rejestracja protokołu napiprojekt: ...")
    if sys.platform == "darwin":
        zarejestruj_macos()
    elif sys.platform.startswith("linux"):
        zarejestruj_linux()
    else:
        print(f"Błąd: Nieobsługiwany system: {sys.platform}")
        sys.exit(1)
    print("\n✓ Gotowe! Kliknięcie w link napiprojekt: będzie uruchamiać napihandler.")


# ---------------------------------------------------------------------------
# Pobieranie napisów
# ---------------------------------------------------------------------------

def parsuj_id(argument: str) -> str:
    """Akceptuje 'napiprojekt:HASH', 'napiprojekt://HASH' lub sam hash MD5."""
    match = re.match(r"^(?:napiprojekt:(?://)?)?([a-f0-9]{32})$", argument.strip(), re.IGNORECASE)
    if not match:
        print(f"Błąd: Nieprawidłowy format ID: '{argument}'")
        print("Oczekiwano: napiprojekt:07a1046ccddd59c0ffc7932331a16d63 lub sam hash MD5")
        sys.exit(1)
    return match.group(1).lower()


def pobierz_napisy(film_id: str, jezyk: str = "PL") -> bytes:
    try:
        import requests
    except ImportError:
        print("Błąd: Brak biblioteki 'requests'. Zainstaluj: pip3 install requests")
        sys.exit(1)

    url = "http://napiprojekt.pl/api/api-napiprojekt3.php"
    payload = {
        "mode": "17",
        "client": "NapiProjekt",
        "client_ver": "2.2.0.2399",
        "user_nick": "",
        "user_password": "",
        "downloaded_subtitles_id": film_id,
        "downloaded_subtitles_lang": jezyk,
        "the": "end",
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Błąd: Brak połączenia z napiprojekt.pl")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Błąd: Przekroczono czas oczekiwania na odpowiedź")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Błąd HTTP: {e}")
        sys.exit(1)

    if response.content[:4] == b"NPc0":
        print("Błąd: Napisy nie zostały znalezione dla podanego ID.")
        sys.exit(1)

    return response.content


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="napihandler",
        description="Pobiera napisy z NapiProjekt — handler protokołu napiprojekt: dla macOS i Linux.",
        epilog=(
            "Przykłady:\n"
            "  napihandler --register\n"
            "  napihandler \"napiprojekt:07a1046ccddd59c0ffc7932331a16d63\"\n"
            "  napihandler 07a1046ccddd59c0ffc7932331a16d63 --jezyk EN -o film.srt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--register",
        action="store_true",
        help="Zarejestruj protokół napiprojekt: w systemie (jednorazowo po instalacji)",
    )
    parser.add_argument(
        "film_id",
        nargs="?",
        help="URI w formacie 'napiprojekt:HASH' lub sam MD5",
    )
    parser.add_argument(
        "--jezyk", "-j",
        default="PL",
        metavar="KOD",
        help="Język napisów, np. PL, EN (domyślnie: PL)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="PLIK",
        help="Nazwa pliku wyjściowego (domyślnie: HASH_JEZYK.srt)",
    )

    args = parser.parse_args()

    if args.register:
        zarejestruj()
        return

    if not args.film_id:
        parser.print_help()
        sys.exit(1)

    film_id = parsuj_id(args.film_id)
    nazwa_pliku = args.output or f"{film_id}_{args.jezyk}.srt"

    print(f"Pobieranie napisów: {film_id} [{args.jezyk}]")
    zawartosc = pobierz_napisy(film_id, args.jezyk)
    Path(nazwa_pliku).write_bytes(zawartosc)
    print(f"✓ Zapisano: {Path(nazwa_pliku).resolve()}")


if __name__ == "__main__":
    main()
