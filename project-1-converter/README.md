# Uniwersalny konwerter plików

Aplikacja desktopowa napisana w języku Python z wykorzystaniem biblioteki Tkinter. Umożliwia bezstratną konwersję plików pomiędzy różnymi formatami, a jej modułowa architektura pozwala na łatwe rozszerzanie obsługiwanych formatów.

Projekt obejmuje trzy grupy konwersji: dane strukturalne, dokumenty tekstowe oraz formaty biurowe. Poprawność działania aplikacji jest weryfikowana za pomocą automatycznych testów jednostkowych i integracyjnych.

---

## Funkcjonalności i Tabela Formatów

Aplikacja obsługuje następujące kierunki konwersji oraz posiada wbudowane ograniczenia zabezpieczające:

### Grupa A — dane strukturalne
| Format źródłowy | Format docelowy | Narzędzie / Biblioteka | Znane ograniczenia |
|---|---|---|---|
| CSV | JSON | Standardowa biblioteka (csv, json) | Wymaga poprawnego pliku w kodowaniu UTF-8 z nagłówkami tabeli. |
| JSON | CSV | Standardowa biblioteka (csv, json) | Struktura JSON musi być płaską listą słowników (obiektów). |

### Grupa B — dokumenty tekstowe
| Format źródłowy | Format docelowy | Narzędzie / Biblioteka | Znane ograniczenia |
|---|---|---|---|
| TXT | DOCX | python-docx | Przenosi czysty tekst akapitami bez zaawansowanego formatowania stylów. |
| DOCX | TXT | python-docx | Ekstrahuje wyłącznie tekst z akapitów (pomija osadzone tabele i obrazy). |
| TXT | ODT | LibreOffice (Headless) | Wymaga poprawnej instalacji pakietu LibreOffice w systemie. |
| ODT | TXT | LibreOffice (Headless) | Wymaga poprawnej instalacji pakietu LibreOffice w systemie. |

### Grupa C — formaty biurowe i PDF
Konwersje w tej grupie są realizowane z wykorzystaniem programu LibreOffice w trybie bez interfejsu graficznego (headless).

| Format źródłowy | Format docelowy | Znane ograniczenia |
|---|---|---|
| TXT / DOCX / ODT | PDF | Wymaga zainstalowanego LibreOffice i dostępu do niego w zmiennej PATH. |
| DOCX ⇄ ODT | ODT / DOCX | Zachowuje strukturę dokumentu, złożone makra lub niestandardowe czcionki mogą być pominięte. |

---

## Wymagania systemowe

Do uruchomienia aplikacji wymagane są:
- Python 3+
- Biblioteka Tkinter (zazwyczaj domyślnie instalowana z Pythonem na Windowsie; na Linuksie wymaga pakietu systemowego python3-tk).
- Pakiet LibreOffice — wymagany wyłącznie do konwersji formatów biurowych i PDF (Grupa C). Aplikacja automatycznie wykrywa jego obecność w systemie (shutil.which oraz domyślne ścieżki).

### Instalacja LibreOffice oraz zależności systemowych

* **Linux (Ubuntu, Debian, Linux Mint):**
  ```bash
  sudo apt update
  sudo apt install libreoffice python3-tk python3-venv
  ```

* **Windows i macOS:**
  Pobierz i zainstaluj stabilną wersję LibreOffice (https://www.libreoffice.org/). Instalator domyślnie dodaje aplikację do zmiennych środowiskowych systemowych (PATH).

---

## Instalacja i uruchomienie (Krok po kroku)

Zaleca się bezwzględne korzystanie z wirtualnego środowiska Python (venv), aby odizolować zależności projektu.

### Dla systemu Linux / macOS:
```bash
# 1. Przejdź do katalogu projektu
cd project-1-converter

# 2. Utwórz wirtualne środowisko
python3 -m venv venv

# 3. Aktywuj środowisko
source venv/bin/activate

# 4. Zainstaluj wymagane pakiety Pythona
pip install -r requirements.txt

# 5. Uruchom aplikację graficzną
python3 gui.py
```
*Uwaga: Jeżeli 'python3 gui.py' wywołuje błędy - należy użyć 'python gui.py'*

### Dla systemu Windows (PowerShell):
```powershell
# 1. Przejdź do katalogu projektu
cd project-1-converter

# 2. Utwórz wirtualne środowisko
python -m venv venv

# 3. Aktywuj środowisko (PowerShell)
.\venv\Scripts\Activate.ps1

# 4. Zainstaluj wymagane pakiety Pythona
pip install -r requirements.txt

# 5. Uruchom aplikację graficzną
python gui.py
```

*Uwaga: Jeżeli w systemie Windows występuje problem z polityką wykonywania skryptów w PowerShell, wykonaj jednorazowo w terminalu jako Administrator: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser.*

---

## Testy automatyczne i Raport z testów

Projekt zawiera automatyczny zestaw testów jednostkowych i integracyjnych (pytest), który w pełni pokrywa minimalną macierz testów:
1. **Poprawne pliki:** Poprawna konwersja danych (np. CSV do JSON) z uwzględnieniem polskich znaków (kodowanie UTF-8).
2. **Błędne pliki:** Obsługa uszkodzonych struktur (np. plik sample_bad.json) zapobiegająca awarii programu.
3. **Nieobsługiwane pary:** Weryfikacja odrzucania niepoprawnych kombinacji rozszerzeń przez metodę validate().
4. **Brak zależności:** Kontrola zachowania systemu w przypadku braku LibreOffice (zgłoszenie RuntimeError).
5. **Konflikt nazw i nadpisywanie:** Sprawdzenie istnienia pliku docelowego zabezpieczone oknem dialogowym w GUI.

### Uruchamianie testów:
Upewnij się, że wirtualne środowisko jest aktywowane, a następnie wykonaj w katalogu projektu:
```bash
pytest
```
Wszystkie testy powinny zakończyć się statusem PASSED.

---

## Struktura projektu

```text
project-1-converter/
├── converter.py         # Logika biznesowa, rejestr konwerterów na dekoratorach i walidacja
├── gui.py               # Graficzny interfejs użytkownika Tkinter (wielowątkowy, non-blocking)
├── conftest.py          # Konfiguracja środowiska testowego pytest
├── requirements.txt     # Zewnętrzne zależności Pythona
├── tests/
│   └── test_converter.py# Zautomatyzowane testy jednostkowe i integracyjne
└── data/
    ├── sample.csv       # Przykładowe dane CSV
    ├── sample.json      # Przykładowe dane JSON
    ├── sample.txt       # Przykładowy tekst
    └── sample_bad.json  # Celowo uszkodzony plik JSON do testów odporności
```

---

## Źródła, Biblioteki i Narzędzia AI
* **Wykorzystane biblioteki:** python-docx, tkinter, pytest, pathlib, subprocess, csv, json.
* **Narzędzia AI:** Projekt realizowany przy wsparciu modeli językowych AI (Google Gemini) w zakresie optymalizacji wielowątkowości GUI oraz generowania przypadków testowych.

---

## Autorzy
* **Student:** Anna Sonchak