# napihandler

Pobiera napisy z [NapiProjekt](http://napiprojekt.pl) przez protokół `napiprojekt:` na macOS, Linux i Windows.

## Instalacja

Pobierz binarkę z [Releases](../../releases) i umieść w PATH:

```bash
# Linux / macOS
chmod +x napihandler-linux   # lub napihandler-macos
sudo mv napihandler-linux /usr/local/bin/napihandler

# Windows
# Umieść napihandler-windows-x86_64.exe w wybranym folderze
```

Jednorazowo zarejestruj protokół w systemie:

```bash
napihandler --register
```

## Użycie

### Kliknięcie w link na stronie NapiProjekt
Po rejestracji kliknięcie w link `napiprojekt:HASH` automatycznie pobierze napisy
do bieżącego katalogu.

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

## Budowanie ze źródeł

```bash
pip3 install pyinstaller requests
python3 build/build.py
```

Binarka trafia do `dist/napihandler`.

## Struktura projektu

```
napihandler/
├── src/
│   └── napihandler.py   # główny skrypt (logika + rejestracja protokołu)
├── build/
│   └── build.py         # buduje binarkę przez PyInstaller
├── dist/
│   └── napihandler      # binarka (po zbudowaniu)
└── README.md
```

## Jak działa hash MD5?

NapiProjekt identyfikuje filmy po MD5 liczonym z **pierwszych 10 MB** pliku wideo.
Hash widoczny w linku `napiprojekt:HASH` na stronie to właśnie ten identyfikator.

## Website
[NapiHandler](https://leonekwolfik.github.io/napihandler/)
