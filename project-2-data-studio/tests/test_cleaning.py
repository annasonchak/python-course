import pandas as pd
import pytest

from studio.cleaning import (
    drop_exact_duplicates,
    drop_rows_with_missing,
    fill_missing_with_constant,
)
from studio.errors import ValidationError
from studio.session import DataSession

def make_frame_with_duplicate() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 2, 3],
        "group": ["A", "B", "B", "B"],
    })


def test_drop_exact_duplicates_removes_only_full_copies():
    session = DataSession(make_frame_with_duplicate())

    removed_count = drop_exact_duplicates(session)

    assert removed_count == 1
    assert len(session.current) == 3
    assert session.current["id"].tolist() == [1, 2, 3]


def test_drop_exact_duplicates_does_not_change_raw():
    session = DataSession(make_frame_with_duplicate())

    drop_exact_duplicates(session)

    assert len(session.raw) == 4


def test_drop_exact_duplicates_writes_audit_entry():
    session = DataSession(make_frame_with_duplicate())

    drop_exact_duplicates(session)

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "drop_exact_duplicates"
    assert last_entry.rows_before == 4
    assert last_entry.rows_after == 3
    assert last_entry.affected == 1


def test_drop_exact_duplicates_when_none_found_changes_nothing():
    session = DataSession(pd.DataFrame({"id": [1, 2, 3]}))

    removed_count = drop_exact_duplicates(session)

    assert removed_count == 0
    assert len(session.current) == 3
    assert session.audit_log[-1].affected == 0

def make_frame_with_missing() -> pd.DataFrame:
    return pd.DataFrame({
        "id": [1, 2, 3],
        "value": [10.0, None, 30.0],
        "group": ["A", "B", None],
    })


def test_drop_rows_with_missing_removes_rows_missing_in_selected_column():
    session = DataSession(make_frame_with_missing())

    removed_count = drop_rows_with_missing(session, ["value"])

    assert removed_count == 1
    assert session.current["id"].tolist() == [1, 3]


def test_drop_rows_with_missing_ignores_other_columns():
    session = DataSession(make_frame_with_missing())

    removed_count = drop_rows_with_missing(session, ["group"])

    assert removed_count == 1
    assert session.current["id"].tolist() == [1, 2]


def test_drop_rows_with_missing_does_not_change_raw():
    session = DataSession(make_frame_with_missing())

    drop_rows_with_missing(session, ["value"])

    assert len(session.raw) == 3


def test_drop_rows_with_missing_writes_audit_entry():
    session = DataSession(make_frame_with_missing())

    drop_rows_with_missing(session, ["value"])

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "drop_rows_with_missing"
    assert last_entry.rows_before == 3
    assert last_entry.rows_after == 2
    assert last_entry.affected == 1


def test_fill_missing_with_constant_in_numeric_column():
    session = DataSession(make_frame_with_missing())

    filled_count = fill_missing_with_constant(session, ["value"], "0")

    assert filled_count == 1
    assert session.current["value"].tolist() == [10.0, 0.0, 30.0]
    assert len(session.current) == 3


def test_fill_missing_with_constant_in_text_column():
    session = DataSession(make_frame_with_missing())

    fill_missing_with_constant(session, ["group"], "brak")

    assert session.current["group"].tolist() == ["A", "B", "brak"]
    assert session.raw["group"].isna().sum() == 1


def test_fill_missing_with_constant_writes_audit_entry():
    session = DataSession(make_frame_with_missing())

    fill_missing_with_constant(session, ["value", "group"], "0")

    last_entry = session.audit_log[-1]
    assert last_entry.operation == "fill_missing_with_constant"
    assert last_entry.rows_before == 3
    assert last_entry.rows_after == 3
    assert last_entry.affected == 2


def test_fill_numeric_column_with_text_raises_and_changes_nothing():
    session = DataSession(make_frame_with_missing())

    with pytest.raises(ValidationError, match="nie jest liczbą"):
        fill_missing_with_constant(session, ["value"], "abc")

    assert session.current["value"].isna().sum() == 1
    assert len(session.audit_log) == 0


def test_cleaning_without_selected_columns_raises_validation_error():
    session = DataSession(make_frame_with_missing())

    with pytest.raises(ValidationError, match="Nie wybrano"):
        drop_rows_with_missing(session, [])


def test_cleaning_with_unknown_column_raises_validation_error():
    session = DataSession(make_frame_with_missing())

    with pytest.raises(ValidationError, match="nie istnieje"):
        fill_missing_with_constant(session, ["nie_ma_takiej"], "0")