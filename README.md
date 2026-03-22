# napihandler

Pobiera napisy z [NapiProjekt](http://napiprojekt.pl) przez protokół `napiprojekt:` na macOS i Linux.

## Budowanie binarki

```bash
pip3 install pyinstaller requests
python3 build/build.py
```

Binarka trafia do `dist/napihandler` — jeden plik, zero zależności.

Aby zainstalować globalnie:
```bash
sudo cp dist/napihandler /usr/local/bin/napihandler
```

## Rejestracja protokołu napiprojekt:

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
napihandler "napiprojekt:07a1046ccddd59c0ffc7932331a16d63"

# Sam hash MD5
napihandler 07a1046ccddd59c0ffc7932331a16d63

# Inny język
napihandler "napiprojekt:07a1046ccddd59c0ffc7932331a16d63" --jezyk EN

# Własna nazwa pliku
napihandler "napiprojekt:07a1046ccddd59c0ffc7932331a16d63" -o film.srt
```

---

## Struktura projektu

```
napihandler/
├── src/
│   └── napihandler.py      # główny skrypt
├── build/
│   ├── build.py            # buduje binarkę przez PyInstaller
│   ├── install_macos.py    # rejestruje protokół na macOS
│   └── install_linux.py    # rejestruje protokół na Linux
├── dist/
│   └── napihandler         # binarka (po zbudowaniu)
└── README.md
```

## Jak działa hash MD5?

NapiProjekt identyfikuje filmy po MD5 liczonym z **pierwszych 10 MB** pliku wideo.
Hash widoczny w linku `napiprojekt:HASH` na stronie to właśnie ten identyfikator.
