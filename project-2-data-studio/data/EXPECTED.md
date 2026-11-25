# Oczekiwane wyniki dla plików testowych

| Plik | Oczekiwany wynik |
|---|---|
| test_01_przecinek.csv | 3 rekordy, 3 kolumny: id, value, group |
| test_02_srednik.csv | Jak test_01 (separator wykryty automatycznie) |
| test_03_braki_duplikaty.csv | 5 rekordów, 1 pełny duplikat, braki: value 2, group 1. Po czyszczeniu: 4 rekordy, value uzupełnione medianą (30), group dominantą (A) |
| test_04_zakres_outlier.csv | HouseAge = -5 poza zakresem 0-100, AveRooms = 1000 wykryte metodą IQR. Pipeline niczego nie usuwa, tylko raportuje, Raport pokazuje oba  problemy: AveRooms=1000 (IQR) i HouseAge=-5 (reguła zakresu 0-100) |
| test_05_bledne_wiersze.csv | Kontrolowany błąd DataLoadError (wiersz z dodatkowym polem) |
| test_06_stala_tekst.csv | Kolumna constant jest stała (IQR = 0, brak odstających); wykres dla niej ma być zablokowany (Lab. 7) |
| california_housing_z_problemami.csv | Duży zbiór referencyjny od prowadzącego, nie jest w repozytorium |