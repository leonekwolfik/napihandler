#!/usr/bin/env python3
"""
napihandler — pobiera napisy z NapiProjekt przez protokół napiprojekt:
Użycie: napihandler "napiprojekt:HASH" [-o plik.srt] [--jezyk EN]
"""

import argparse
import re
import sys
from pathlib import Path

import requests


def parsuj_id(argument: str) -> str:
    """Akceptuje 'napiprojekt:HASH' lub sam hash MD5."""
    match = re.match(r"^(?:napiprojekt:)?([a-f0-9]{32})$", argument.strip(), re.IGNORECASE)
    if not match:
        print(f"Błąd: Nieprawidłowy format ID: '{argument}'")
        print("Oczekiwano: napiprojekt:07a1046ccddd59c0ffc7932331a16d63 lub sam hash MD5")
        sys.exit(1)
    return match.group(1).lower()


def pobierz_napisy(film_id: str, jezyk: str = "PL") -> bytes:
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


def zapisz_napisy(zawartosc: bytes, nazwa_pliku: str):
    path = Path(nazwa_pliku)
    path.write_bytes(zawartosc)
    print(f"✓ Zapisano napisy: {path.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        prog="napihandler",
        description="Pobiera napisy z NapiProjekt — handler protokołu napiprojekt: dla macOS i Linux.",
        epilog="Przykład: napihandler \"napiprojekt:07a1046ccddd59c0ffc7932331a16d63\"",
    )
    parser.add_argument(
        "film_id",
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

    film_id = parsuj_id(args.film_id)
    nazwa_pliku = args.output or f"{film_id}_{args.jezyk}.srt"

    print(f"Pobieranie napisów: {film_id} [{args.jezyk}]")
    zawartosc = pobierz_napisy(film_id, args.jezyk)
    zapisz_napisy(zawartosc, nazwa_pliku)


if __name__ == "__main__":
    main()