import pandas as pd

from studio.cleaning import drop_exact_duplicates
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