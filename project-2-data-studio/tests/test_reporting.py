import pandas as pd
import pytest

from studio.cleaning import drop_exact_duplicates
from studio.errors import ValidationError
from studio.plots import histogram_figure
from studio.reporting import (
    build_audit_report_text,
    build_audit_table,
    save_audit_report,
    save_cleaned_csv,
    save_figure,
)
from studio.session import DataSession

def make_session_with_operation() -> DataSession:
    frame = pd.DataFrame({
        "id": [1, 2, 2, 3],
        "name": ["Łukasz", "Ala", "Ala", "Zażółć"],
    })
    session = DataSession(frame)
    drop_exact_duplicates(session)
    return session


def test_report_text_contains_operation_and_counts():
    session = make_session_with_operation()

    text = build_audit_report_text(session)

    assert "drop_exact_duplicates" in text
    assert "4 -> 3" in text
    assert "Rekordy w danych surowych: 4" in text


def test_report_text_without_operations_says_so():
    session = DataSession(pd.DataFrame({"x": [1]}))

    assert "Nie wykonano żadnych operacji" in build_audit_report_text(session)


def test_audit_table_has_one_row_per_operation():
    session = make_session_with_operation()

    table = build_audit_table(session)

    assert len(table) == 1
    assert table.loc[0, "affected"] == 1


def test_save_audit_report_as_txt_and_csv(tmp_path):
    session = make_session_with_operation()

    txt_path = save_audit_report(session, tmp_path / "raport.txt")
    csv_path = save_audit_report(session, tmp_path / "raport.csv")

    assert "RAPORT ZMIAN" in txt_path.read_text(encoding="utf-8")
    assert len(pd.read_csv(csv_path)) == 1


def test_save_audit_report_with_unknown_extension_raises(tmp_path):
    session = make_session_with_operation()

    with pytest.raises(ValidationError, match="Nieobsługiwane rozszerzenie"):
        save_audit_report(session, tmp_path / "raport.docx")


def test_cleaned_csv_can_be_read_again_with_polish_characters(tmp_path):
    session = make_session_with_operation()

    path = save_cleaned_csv(session, tmp_path / "cleaned.csv")
    reloaded = DataSession.from_csv(path)

    assert reloaded.raw["name"].tolist() == ["Łukasz", "Ala", "Zażółć"]
    assert reloaded.raw.shape == (3, 2)


def test_save_to_missing_folder_raises_validation_error(tmp_path):
    session = make_session_with_operation()

    with pytest.raises(ValidationError, match="Nie można zapisać"):
        save_cleaned_csv(session, tmp_path / "nie_ma_folderu" / "cleaned.csv")

def make_figure():
    session = DataSession(pd.DataFrame({"x": [1, 2, 3, 4, 10]}))
    return histogram_figure(session, "x")


def test_save_figure_png_pdf_svg_are_not_empty(tmp_path):
    figure = make_figure()

    for name in ["w.png", "w.pdf", "w.svg"]:
        saved = save_figure(figure, tmp_path / name)
        assert saved.stat().st_size > 0


def test_save_figure_unknown_extension_raises(tmp_path):
    with pytest.raises(ValidationError, match="Nieobsługiwane rozszerzenie"):
        save_figure(make_figure(), tmp_path / "w.bmp")


def test_save_figure_to_missing_folder_raises(tmp_path):
    with pytest.raises(ValidationError, match="Nie można zapisać"):
        save_figure(make_figure(), tmp_path / "nie_ma" / "w.png")