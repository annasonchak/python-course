import pandas as pd

from studio.session import DataSession


def make_frame() -> pd.DataFrame:
    return pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})


def test_current_is_independent_copy_of_raw():
    session = DataSession(make_frame())
    session.current.loc[0, "x"] = 99
    assert session.raw.loc[0, "x"] == 1


def test_reset_restores_raw_data():
    session = DataSession(make_frame())
    session.current = session.current.iloc[:1]
    session.reset()
    assert session.current.equals(session.raw)


def test_reset_is_written_to_audit_log():
    session = DataSession(make_frame())
    session.current = session.current.iloc[:1]
    session.reset()
    last_entry = session.audit_log[-1]
    assert last_entry.operation == "reset"
    assert last_entry.rows_before == 1
    assert last_entry.rows_after == 3