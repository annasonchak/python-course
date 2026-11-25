from pathlib import Path

import pytest

from studio.errors import DataLoadError
from studio.session import DataSession

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def write_file(path: Path, text: str, encoding: str = "utf-8") -> Path:
    path.write_bytes(text.encode(encoding))
    return path

def test_comma_and_semicolon_give_same_columns():
    comma_session = DataSession.from_csv(DATA_DIR / "test_01_przecinek.csv")
    semicolon_session = DataSession.from_csv(DATA_DIR / "test_02_srednik.csv")

    expected_columns = ["id", "value", "group"]
    assert list(comma_session.raw.columns) == expected_columns
    assert list(semicolon_session.raw.columns) == expected_columns
    assert comma_session.raw.shape == (3, 3)
    assert semicolon_session.raw.shape == (3, 3)

def test_polish_characters_in_cp1250(tmp_path):
    path = write_file(tmp_path / "pl.csv", "miasto;temp\nŁódź;10\nGdańsk;8\n", "cp1250")
    session = DataSession.from_csv(path)
    assert session.raw["miasto"].tolist() == ["Łódź", "Gdańsk"]

def test_empty_file_raises_data_load_error(tmp_path):
    path = write_file(tmp_path / "empty.csv", "")
    with pytest.raises(DataLoadError, match="pusty"):
        DataSession.from_csv(path)

def test_header_only_file_raises_data_load_error(tmp_path):
    path = write_file(tmp_path / "header.csv", "a,b\n")
    with pytest.raises(DataLoadError, match="rekordów"):
        DataSession.from_csv(path)

def test_missing_file_raises_data_load_error(tmp_path):
    with pytest.raises(DataLoadError, match="nie istnieje"):
        DataSession.from_csv(tmp_path / "nie_ma.csv")

def test_bad_rows_file_raises_data_load_error():
    with pytest.raises(DataLoadError, match="Wadliwy wiersz"):
        DataSession.from_csv(DATA_DIR / "test_05_bledne_wiersze.csv")