"""Operacje czyszczenia danych na session.current"""
from __future__ import annotations

from studio.session import DataSession


def drop_exact_duplicates(session: DataSession) -> int:
    """Usuwa pełne duplikaty, zwraca liczbę usuniętych"""
    rows_before = len(session.current)

    cleaned_frame = session.current.drop_duplicates(keep="first")
    session.current = cleaned_frame.copy()

    removed_count = rows_before - len(session.current)

    session.record(
        operation="drop_exact_duplicates",
        params={"keep": "first"},
        rows_before=rows_before,
        affected=removed_count,
    )
    return removed_count