# napihandler

Pobiera napisy z [NapiProjekt](http://napiprojekt.pl) przez protokół `napiprojekt:` na macOS i Linux.

## Wymagania

```bash
pip3 install requests
```

## Instalacja

### macOS
```bash
python3 build/install_macos.py
```
Tworzy aplikację `NapiHandler.app` w `~/Applications` i rejestruje protokół `napiprojekt:` w systemie.

### Linux
```bash
python3 build/install_linux.py
```
Tworzy plik `.desktop` i rejestruje protokół przez `xdg-mime`. Działa z GNOME, KDE, XFCE i innymi.

---

## Użycie

### Kliknięcie w link na stronie NapiProjekt
Po instalacji kliknięcie w link `napiprojekt:HASH` automatycznie pobierze napisy do bieżącego katalogu.

### CLI
```bash
# URI ze strony
python3 napihandler.py "napiprojekt:07a1046ccddd59c0ffc7932331a16d63"

# Sam hash MD5
python3 napihandler.py 07a1046ccddd59c0ffc7932331a16d63

# Inne język
python3 napihandler.py "napiprojekt:07a1046ccddd59c0ffc7932331a16d63" --jezyk EN

# Własna nazwa pliku
python3 napihandler.py "napiprojekt:07a1046ccddd59c0ffc7932331a16d63" -o film.srt
```

Po dodaniu do PATH (przez install_linux.py / install_macos.py):
```bash
napihandler "napiprojekt:07a1046ccddd59c0ffc7932331a16d63"
```

---

## Struktura projektu

```
napihandler/
├── src/
│   └── napihandler.py      # główny skrypt
├── build/
│   ├── install_macos.py    # instalator dla macOS
│   └── install_linux.py    # instalator dla Linux
└── README.md
```

## Jak działa hash MD5?

NapiProjekt identyfikuje filmy po MD5 liczonym z **pierwszych 10 MB** pliku wideo.
Hash widoczny w linku `napiprojekt:HASH` na stronie to właśnie ten identyfikator.