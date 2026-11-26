# Studio jakości i wizualizacji danych

Aplikacja desktopowa w Pythonie (Tkinter/ttk), która prowadzi użytkownika od wczytania pliku CSV, przez diagnozę i czyszczenie danych, do wizualizacji i eksportu wyników. Każda operacja jest zapisywana w dzienniku zmian, więc użytkownik widzi, co i dlaczego zmieniło zbiór.

---

## Funkcjonalności

### Wczytywanie i profil danych
- Separator `,` `;` lub tabulator wykrywany automatycznie (na podstawie nagłówka).
- Kodowanie UTF-8 z awaryjnym `cp1250` (polskie pliki z Excela).
- Kontrolowane błędy: brak pliku, plik pusty, tylko nagłówek, wadliwy wiersz, nieznane kodowanie. Aplikacja nie zamyka się.
- Podgląd pierwszych 100 rekordów.
- Profil: liczba rekordów i kolumn, typy, statystyki opisowe, liczba i procent braków, pełne duplikaty, liczba unikalnych wartości.

### Czyszczenie (zawsze na kopii, dane surowe są nietykalne)
- Usuwanie pełnych duplikatów (pierwsze wystąpienie zostaje).
- Braki: usunięcie rekordów, stała, średnia, mediana, dominanta.
- Reguła zakresu (minimum i/lub maksimum): najpierw tylko wykrywa, zmiana następuje po decyzji użytkownika (zamiana na brak albo usunięcie rekordów, z potwierdzeniem).
- Wartości odstające metodą IQR (współczynnik konfigurowalny): `flag`, `clip`, `drop`, `keep`, również z potwierdzeniem.
- Reset do danych surowych bez ponownego uruchamiania programu.

### Ślad zmian
Dziennik zawiera operację, parametry, czas, liczbę rekordów przed i po oraz liczbę dotkniętych rekordów. Widoczny w oknie, eksportowany do `.txt` i `.csv`. Reset nie czyści dziennika (historia zostaje).

### Wizualizacje
Histogram, wykres punktowy, pudełkowy, słupkowy oraz mapa korelacji (Pearson). Każdy wykres ma tytuł i opisy osi. Niepoprawny wybór (kolumna stała, tekstowa, ta sama kolumna na obu osiach, zbyt wiele kategorii) jest blokowany z komunikatem. Wykresy punktowy i korelacji zawierają ostrzeżenie, że korelacja nie oznacza przyczynowości.

### Eksport
Oczyszczony CSV (UTF-8), raport zmian (TXT/CSV), wykres (PNG, PDF, SVG).

---

## Wymagania

- Python 3.10+
- Tkinter (Linux: `sudo apt install python3-tk python3-venv`)
- Pakiety z `requirements.txt`: pandas, matplotlib, seaborn, pytest

## Instalacja i uruchomienie

### Linux / macOS
```bash
cd project-2-data-studio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Windows (PowerShell)
```powershell
cd project-2-data-studio
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Skrypty pomocnicze

```bash
python run_pipeline.py data/test_03_braki_duplikaty.csv   # raport przed/po, zapis do output/
python make_output.py                                     # pliki do oddania: cleaned.csv, raport, wykresy
```

---

## Reguły czyszczenia i uzasadnienie

### Braki
| Strategia | Kiedy |
|---|---|
| usunięcie rekordów | gdy braków jest mało i rekord bez wartości jest bezużyteczny |
| stała | gdy brak ma znaczenie (np. "brak" w kolumnie tekstowej, 0 w liczbowej) |
| średnia | dane liczbowe bez silnych wartości skrajnych |
| mediana | dane liczbowe z wartościami skrajnymi (odporna na odstające) |
| dominanta | kolumny kategorialne |

Przy równej liczbie wystąpień dominanta wybiera pierwszą wartość alfabetycznie.

### Duplikaty
Usuwane są tylko rekordy identyczne we wszystkich kolumnach. Rekord różniący się choćby jedną wartością (np. `id`) nie jest duplikatem.

### Wartości spoza zakresu a odstające
To dwa różne mechanizmy:
- **Reguła zakresu** sprawdza, czy wartość jest dopuszczalna merytorycznie (wiek budynku nie może być ujemny).
- **IQR** sprawdza, czy wartość jest statystycznie daleko od reszty danych.

Przykład z `test_04_zakres_outlier.csv`: `AveRooms = 1000` wykrywa IQR, a `HouseAge = -5` jest w granicach IQR (rozrzut kolumny jest duży) i wykrywa je dopiero reguła zakresu 0-100. Stąd potrzeba obu.

### Metoda IQR
Granice: `[Q1 - k*IQR, Q3 + k*IQR]`, domyślnie k = 1,5. Wybrana, bo opiera się na kwartylach, które same są odporne na wartości skrajne (średnia i odchylenie standardowe nie są). Gdy IQR = 0 (kolumna stała), odstających nie wykrywamy.

### Decyzja wobec wartości odstających
Aplikacja nigdy nie usuwa odstających automatycznie. Użytkownik widzi regułę i liczbę znalezionych wartości, a zmiana wymaga potwierdzenia.

| Akcja | Kiedy |
|---|---|
| `flag` | nie wiadomo, czy to błąd, dodaje kolumnę `<nazwa>_outlier`, wartości bez zmian |
| `clip` | wartość prawdopodobnie realna, ale zniekształca analizę, rekord zostaje (przycięcie do granic) |
| `drop` | oczywisty błąd pomiaru |
| `keep` | wartość realna i ważna, tylko odnotowana w dzienniku |

Przykład w `output/`: `HouseAge = -5` to błąd (zakres, zamiana na brak, mediana), a `AveRooms = 1000` jest przycięte (`clip`) do górnej granicy IQR.

---

## Architektura

```text
project-2-data-studio/
├── main.py                  # punkt wejścia
├── run_pipeline.py          # skrypt: raport przed/po
├── make_output.py           # generuje pliki do oddania
├── requirements.txt
├── conftest.py
├── studio/
│   ├── errors.py            # własne wyjątki (StudioError, DataLoadError, ValidationError)
│   ├── session.py           # DataSession: raw, current, dziennik, reset, wczytywanie CSV
│   ├── profiling.py         # profil danych
│   ├── cleaning.py          # operacje czyszczenia
│   ├── plots.py             # wykresy (zwracają Figure)
│   ├── reporting.py         # zapis CSV, raportu i wykresów
│   └── gui.py               # Tkinter, bez logiki biznesowej
├── tests/
├── data/                    # pliki testowe i EXPECTED.md
└── output/                  # przykładowe wyniki
```

Zasady: moduły w `studio/` (poza `gui.py`) nie znają Tkintera. Dane surowe (`raw`) nie są modyfikowane, operacje działają na `current`. Funkcje wykresów zwracają `Figure`, więc ten sam wykres można osadzić w oknie i zapisać do pliku. Stan aplikacji jest polem obiektu `App`, bez zmiennych globalnych.

---

## Testy

```bash
pytest -v
```

Wynik: **114 passed**.

| Obszar | Plik |
|---|---|
| Wczytywanie (separatory, cp1250, błędne pliki) | `tests/test_loading.py` |
| Sesja i dziennik | `tests/test_session.py`, `tests/test_audit.py` |
| Profil | `tests/test_profile.py` |
| Czyszczenie | `tests/test_cleaning.py` |
| Wykresy i walidacja | `tests/test_plots.py` |
| Raport i zapis | `tests/test_reporting.py` |
| Pełny cykl eksportu i ponowny odczyt | `tests/test_export.py` |
| Pipeline | `tests/test_pipeline.py` |
| GUI (smoke) | `tests/test_gui.py` |

Testy logiki używają małych, ręcznie zbudowanych ramek danych. Oczekiwane wyniki plików testowych: `data/EXPECTED.md`.

### Testy GUI (ręczne)

| Scenariusz | Oczekiwany wynik | Wynik |
|---|---|---|
| Wczytanie test_01 i test_02 | 3 rekordy, 3 kolumny, profil w tabeli | OK |
| Wczytanie test_05 | Okno błędu, aplikacja działa dalej | OK |
| Usuń duplikaty na test_03 | Status: usunięto 1, wpis w dzienniku | OK |
| Reguła zakresu HouseAge 0-100 na test_04 | Sprawdź: 1 wartość, dane bez zmian | OK |
| Histogram dla kolumny tekstowej | Okno z komunikatem, brak wykresu | OK |
| Wykres dla kolumny stałej (test_06) | Komunikat "jest stała" | OK |
| Zmiana typu wykresu | Poprzedni wykres zastąpiony | OK |
| Zapis CSV, PNG, PDF, SVG | Pliki otwierają się poprawnie | OK |

---

## Znane ograniczenia

- Korelacja liczona tylko metodą Pearsona, tylko dla kolumn liczbowych niestałych.
- Wykres słupkowy ma limit 20 kategorii.
- Podgląd danych pokazuje pierwsze 100 rekordów.
- Reguła zakresu i IQR działają na jednej kolumnie naraz.
- Test GUI wymaga środowiska graficznego (bez niego jest pomijany).
- Zbiór `california_housing_z_problemami.csv` jest duży i nie znajduje się w repozytorium.

---

## Źródła, biblioteki i narzędzia

- **Biblioteki:** pandas, matplotlib, seaborn, tkinter, pytest, pathlib.
- **Dokumentacja:** pandas (`read_csv`, User Guide), Matplotlib (Embed in Tk), Seaborn (tutorial), materiały pomocnicze do instrukcji projektowej.
- **Narzędzia AI:** Claude (Anthropic) został użyty jako wsparcie w projektowaniu architektury, przy generowaniu szkiców kodu modułów i testów jednostkowych oraz przy diagnozowaniu błędów. Historia pracy jest widoczna w commitach.

---

## Autorzy

* **Student:** Anna Sonchak