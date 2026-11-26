import dataclasses

import pytest

from studio.session import AuditEntry


def test_audit_entry_stores_fields_and_timestamp():
    entry = AuditEntry("drop_duplicates", {"subset": None}, rows_before=10, rows_after=8, affected=2)
    assert entry.operation == "drop_duplicates"
    assert entry.rows_before - entry.rows_after == entry.affected
    assert entry.timestamp


def test_audit_entry_is_immutable():
    entry = AuditEntry("x", {}, 1, 1, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.affected = 5


def test_audit_entry_str_contains_counts():
    text = str(AuditEntry("reset", {}, 5, 10, 5))
    assert "reset" in text and "5 -> 10" in text