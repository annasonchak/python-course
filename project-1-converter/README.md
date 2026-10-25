# Uniwersalny konwerter plików

Aplikacja desktopowa napisana w języku Python z wykorzystaniem biblioteki **Tkinter**. Umożliwia konwersję plików pomiędzy różnymi formatami, a jej modułowa architektura pozwala na łatwe rozszerzanie obsługiwanych formatów.

Projekt obejmuje trzy grupy konwersji: dane strukturalne, dokumenty tekstowe oraz formaty biurowe. Poprawność działania aplikacji jest weryfikowana za pomocą automatycznych testów jednostkowych i integracyjnych.

## Funkcjonalności

Aplikacja obsługuje następujące kierunki konwersji.

### Grupa A — dane strukturalne

| Format źródłowy | Format docelowy | Opis |
|---|---|---|
| CSV | JSON | Konwersja danych tabelarycznych do formatu JSON z zachowaniem nagłówków i kodowania UTF-8. |
| JSON | CSV | Konwersja danych JSON do formatu tabelarycznego CSV. |

### Grupa B — dokumenty tekstowe

| Format źródłowy | Format docelowy |
|---|---|
| TXT | DOCX |
| DOCX | TXT |
| TXT | ODT |
| ODT | TXT |

### Grupa C — formaty biurowe i PDF

Konwersje w tej grupie są realizowane z wykorzystaniem programu LibreOffice w trybie bez interfejsu graficznego (*headless*).

| Format źródłowy | Format docelowy |
|---|---|
| TXT | PDF |
| DOCX | PDF |
| DOCX | ODT |
| ODT | DOCX |
| ODT | PDF |

## Wymagania systemowe

Do uruchomienia aplikacji wymagane są:

- Python 3;
- biblioteka Tkinter;
- pakiety Python wymienione w pliku `requirements.txt`;
- LibreOffice — wymagany do konwersji wykorzystujących jego mechanizm eksportu, w szczególności do formatów PDF i ODT.

### Instalacja LibreOffice

**Linux (Ubuntu, Debian, Linux Mint):**

```bash
sudo apt update
sudo apt install libreoffice python3-tk python3-venv
```

**Windows i macOS:**

Pobierz i zainstaluj LibreOffice z oficjalnej strony:

https://www.libreoffice.org/

Upewnij się, że aplikacja jest dostępna w systemie. Jeśli polecenie `libreoffice` nie jest rozpoznawane, może być konieczne skonfigurowanie ścieżki do programu.

## Instalacja i uruchomienie

Zaleca się korzystanie z wirtualnego środowiska Python (`venv`), aby odizolować zależności projektu od pozostałych pakietów zainstalowanych w systemie.

### Linux i macOS

1. Przejdź do katalogu projektu:

   ```bash
   cd project-1-converter
   ```

2. Utwórz wirtualne środowisko:

   ```bash
   python3 -m venv venv
   ```

3. Aktywuj środowisko:

   ```bash
   source venv/bin/activate
   ```

4. Zainstaluj wymagane pakiety:

   ```bash
   pip install -r requirements.txt
   ```

5. Uruchom aplikację:

   ```bash
   python gui.py
   ```

### Windows

1. Otwórz PowerShell lub wiersz polecenia i przejdź do katalogu projektu:

   ```powershell
   cd project-1-converter
   ```

2. Utwórz wirtualne środowisko:

   ```powershell
   python -m venv venv
   ```

3. Aktywuj środowisko.

   **PowerShell:**

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   **CMD:**

   ```bat
   venv\Scripts\activate.bat
   ```

4. Zainstaluj wymagane pakiety:

   ```bash
   pip install -r requirements.txt
   ```

5. Uruchom aplikację:

   ```bash
   python gui.py
   ```

## Testy automatyczne

Projekt zawiera testy jednostkowe i integracyjne sprawdzające poprawność działania konwerterów oraz obsługę typowych sytuacji wyjątkowych.

Testy obejmują między innymi:

- konwersję plików pomiędzy obsługiwanymi formatami;
- obsługę nieprawidłowych danych JSON;
- zachowanie polskich znaków i kodowania UTF-8;
- obsługę brakujących narzędzi systemowych;
- weryfikację zachowania aplikacji w przypadku błędów konwersji.

### Uruchamianie testów

1. Aktywuj wirtualne środowisko.
2. Upewnij się, że wymagane zależności zostały zainstalowane.
3. W katalogu głównym projektu wykonaj polecenie:

   ```bash
   pytest
   ```

Wyniki testów zostaną wyświetlone w terminalu.

## Struktura projektu

```text
project-1-converter/
├── converter.py
├── gui.py
├── conftest.py
├── requirements.txt
├── tests/
└── data/
    ├── sample.csv
    ├── sample.json
    ├── sample.txt
    └── sample_bad.json
```

### Opis plików i katalogów

| Plik lub katalog | Opis |
|---|---|
| `converter.py` | Implementacja logiki konwersji oraz rejestru konwerterów wykorzystującego dekoratory. |
| `gui.py` | Graficzny interfejs użytkownika oparty na bibliotece Tkinter. |
| `conftest.py` | Konfiguracja środowiska testowego dla pytest. |
| `tests/` | Testy jednostkowe i integracyjne. |
| `data/` | Przykładowe pliki wykorzystywane podczas testowania konwersji. |
| `requirements.txt` | Lista zewnętrznych zależności Python. |

## Architektura

Aplikacja została podzielona na dwie główne warstwy:

- **Warstwa logiki (`converter.py`)** — odpowiada za rejestrowanie konwerterów, wybór odpowiedniej operacji i przetwarzanie plików.
- **Warstwa interfejsu (`gui.py`)** — odpowiada za interakcję z użytkownikiem i udostępnia funkcje konwersji za pomocą graficznego interfejsu.

Taki podział ułatwia testowanie logiki niezależnie od interfejsu graficznego oraz dodawanie kolejnych konwerterów bez konieczności przebudowy całej aplikacji.