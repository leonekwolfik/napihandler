# napihandler

Pobiera napisy z [NapiProjekt](http://napiprojekt.pl) przez protokół `napiprojekt:` na macOS, Linux i Windows.

## Instalacja

Pobierz binarkę z [Releases](../../releases) i umieść w PATH:

### Linux
```bash
chmod +x napihandler-linux-x86_64
sudo mv napihandler-linux-x86_64 /usr/local/bin/napihandler
```

### macOS
```bash
chmod +x napihandler-macos-arm64   # lub napihandler-macos-x86_64 dla Intel
xattr -d com.apple.quarantine napihandler-macos-arm64
sudo mv napihandler-macos-arm64 /usr/local/bin/napihandler
```

### Windows
```bash
# Umieść napihandler-windows-x86_64.exe w wybranym folderze
# Dodaj ten folder do zmiennej środowiskowej PATH, aby móc uruchamiać napihandler z dowolnego miejsca
```

> **macOS – błąd „Apple nie może zweryfikować"**: macOS blokuje pobrane binarki bez certyfikatu Apple Developer.
> Usuń atrybut kwarantanny poleceniem:
> ```bash
> xattr -d com.apple.quarantine napihandler-macos-arm64
> ```

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
