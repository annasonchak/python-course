"""Operacje czyszczenia danych na session.current"""
from __future__ import annotations

import pandas as pd

from studio.errors import ValidationError
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

def validate_columns(session: DataSession, columns: list[str]) -> None:
    """Sprawdza, czy użytkownik wybrał kolumny i czy one istnieją"""
    if len(columns) == 0:
        raise ValidationError(
            "Nie wybrano żadnej kolumny. Zaznacz co najmniej jedną kolumnę"
        )

    for column_name in columns:
        if column_name not in session.current.columns:
            raise ValidationError(
                f"Kolumna '{column_name}' nie istnieje w danych. Wybierz kolumnę z listy"
            )


def drop_rows_with_missing(session: DataSession, columns: list[str]) -> int:
    """Usuwa rekordy, które mają brak w którejkolwiek z wybranych kolumn"""
    validate_columns(session, columns)
    rows_before = len(session.current)

    cleaned_frame = session.current.dropna(subset=columns)
    session.current = cleaned_frame.copy()

    removed_count = rows_before - len(session.current)

    session.record(
        operation="drop_rows_with_missing",
        params={"columns": columns},
        rows_before=rows_before,
        affected=removed_count,
    )
    return removed_count


def fill_missing_with_constant(session: DataSession, columns: list[str], value: str) -> int:
    """Wypełnia braki stałą wartością w wybranych kolumnach. Zwraca liczbę wypełnionych braków"""
    validate_columns(session, columns)
    rows_before = len(session.current)

    new_frame = session.current.copy()
    filled_count = 0

    for column_name in columns:
        column = new_frame[column_name]
        missing_count = int(column.isna().sum())

        if missing_count == 0:
            continue

        fill_value = value
        if pd.api.types.is_numeric_dtype(column):
            try:
                fill_value = float(value)
            except ValueError:
                raise ValidationError(
                    f"Kolumna '{column_name}' jest liczbowa, a '{value}' nie jest liczbą. "
                    "Wpisz liczbę, na przykład 0 albo 12.5"
                )

        new_frame[column_name] = column.fillna(fill_value)
        filled_count += missing_count

    session.current = new_frame

    session.record(
        operation="fill_missing_with_constant",
        params={"columns": columns, "value": value},
        rows_before=rows_before,
        affected=filled_count,
    )
    return filled_count