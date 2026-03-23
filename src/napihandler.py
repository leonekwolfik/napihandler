#!/usr/bin/env python3
"""
napihandler — downloads subtitles from NapiProjekt via napiprojekt: protocol

Usage:
    napihandler --register                          # one-time protocol registration
    napihandler "napiprojekt:HASH"                  # download subtitles
    napihandler "napiprojekt:HASH" --language EN    # different language
    napihandler "napiprojekt:HASH" -o film.srt      # custom filename
"""

import argparse
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Protocol Registration
# ---------------------------------------------------------------------------


def binary_path() -> Path:
    """Path to the currently running binary (or script)."""
    return Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()


def register_macos():
    exe = binary_path()
    app_dir = Path.home() / "Applications" / "NapiHandler.app"
    macos_dir = app_dir / "Contents" / "MacOS"
    macos_dir.mkdir(parents=True, exist_ok=True)

    # Info.plist — registers napiprojekt scheme:
    plist = app_dir / "Contents" / "Info.plist"
    plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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

    # Launcher — macOS passes URI as argument
    launcher = macos_dir / "napihandler-launcher"
    launcher.write_text(f"""#!/bin/bash
URI=$(echo "$1" | sed 's|napiprojekt://|napiprojekt:|')
"{exe}" "$URI"
""")
    launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Register .app in LaunchServices
    lsregister = (
        "/System/Library/Frameworks/CoreServices.framework/Versions/A"
        "/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
    )
    subprocess.run([lsregister, "-f", str(app_dir)], check=True)

    print(f"OK: Created: {app_dir}")
    print("OK: Registered napiprojekt protocol in system")
    print("  You may need to log out or restart Finder.")


def register_linux():
    exe = binary_path()
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    desktop_file = desktop_dir / "napihandler.desktop"
    desktop_file.write_text(f"""[Desktop Entry]
Name=NapiHandler
Comment=Downloads subtitles from NapiProjekt
Exec="{exe}" %u
Type=Application
NoDisplay=true
MimeType=x-scheme-handler/napiprojekt;
""")
    print(f"OK: Created: {desktop_file}")

    if shutil.which("xdg-mime"):
        subprocess.run(
            [
                "xdg-mime",
                "default",
                "napihandler.desktop",
                "x-scheme-handler/napiprojekt",
            ],
            check=True,
        )
        print("OK: Registered napiprojekt protocol via xdg-mime")
    else:
        print("NOK: xdg-mime not found — run manually:")
        print("xdg-mime default napihandler.desktop x-scheme-handler/napiprojekt")

    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(desktop_dir)], check=True)
        print("OK: Refreshed desktop entries database")


def register_windows():
    exe = binary_path()
    import winreg

    # Registry key for napiprojekt protocol
    key_path = r"Software\Classes\napiprojekt"
    command_key_path = rf"{key_path}\shell\open\command"

    try:
        # Create main protocol key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, None, winreg.REG_SZ, "URL:NapiProjekt Subtitles")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

        # Create command key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
            winreg.SetValue(key, None, winreg.REG_SZ, f'"{exe}" "%1"')

        print("OK: Registered napiprojekt protocol in Windows registry")
        print("  Changes will take effect after restarting browser or system.")

    except Exception as e:
        print(f"Error during Windows registration: {e}")
        print("Try running as administrator.")
        sys.exit(1)


def register():
    print("Registering napiprojekt protocol...")
    if sys.platform == "darwin":
        register_macos()
    elif sys.platform.startswith("linux"):
        register_linux()
    elif sys.platform.startswith("win"):
        register_windows()
    else:
        print(f"Error: Unsupported system: {sys.platform}")
        sys.exit(1)
    print("\nOK: Done! Clicking napiprojekt: links will launch napihandler.")


# ---------------------------------------------------------------------------
# Subtitle Download
# ---------------------------------------------------------------------------


def parse_id(argument: str) -> str:
    """Accepts 'napiprojekt:HASH', 'napiprojekt://HASH' or MD5 hash alone."""
    match = re.match(
        r"^(?:napiprojekt:(?://)?)?([a-f0-9]{32})$", argument.strip(), re.IGNORECASE
    )
    if not match:
        print(f"Error: Invalid ID format: '{argument}'")
        print(
            "Expected: napiprojekt:07a1046ccddd59c0ffc7932331a16d63 or MD5 hash alone"
        )
        sys.exit(1)
    return match.group(1).lower()


def download_subtitles(film_id: str, language: str = "PL") -> bytes:
    try:
        import requests
    except ImportError:
        print("Error: Missing 'requests' library. Install: pip3 install requests")
        sys.exit(1)

    url = "http://napiprojekt.pl/api/api-napiprojekt3.php"
    payload = {
        "mode": "17",
        "client": "NapiProjekt",
        "client_ver": "2.2.0.2399",
        "user_nick": "",
        "user_password": "",
        "downloaded_subtitles_id": film_id,
        "downloaded_subtitles_lang": language,
        "the": "end",
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Error: No connection to napiprojekt.pl")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("Error: Response timeout exceeded")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        sys.exit(1)

    if response.content[:4] == b"NPc0":
        print("Error: Subtitles not found for given ID.")
        sys.exit(1)

    return response.content


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        prog="napihandler",
        description="Downloads subtitles from NapiProjekt — napiprojekt: protocol handler for macOS, Linux and Windows.",
        epilog=(
            "Examples:\n"
            "  napihandler --register\n"
            '  napihandler "napiprojekt:07a1046ccddd59c0ffc7932331a16d63"\n'
            "  napihandler 07a1046ccddd59c0ffc7932331a16d63 --language EN -o film.srt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--register",
        action="store_true",
        help="Register napiprojekt: protocol in system (one-time after installation)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only simulate registration (for testing)",
    )
    parser.add_argument(
        "film_id",
        nargs="?",
        help="URI in 'napiprojekt:HASH' format or MD5 hash alone",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="PL",
        metavar="CODE",
        help="Subtitle language, e.g. PL, EN (default: PL)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Output filename (default: HASH_LANGUAGE.srt)",
    )

    args = parser.parse_args()

    if args.register:
        if args.dry_run:
            print("OK: Napiprojekt protocol registration simulation completed successfully")
            print("  (Used --dry-run - registration was skipped)")
        else:
            register()
        return

    if not args.film_id:
        parser.print_help()
        sys.exit(1)

    film_id = parse_id(args.film_id)
    filename = args.output or f"{film_id}_{args.language}.srt"

    print(f"Downloading subtitles: {film_id} [{args.language}]")
    content = download_subtitles(film_id, args.language)
    Path(filename).write_bytes(content)
    print(f"OK: Saved: {Path(filename).resolve()}")


if __name__ == "__main__":
    main()
