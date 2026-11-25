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

def fill_missing_with_statistic(session: DataSession, columns: list[str], strategy: str) -> int:
    """Wypełnia braki średnią, medianą albo najczęstszą wartością (mean, median, mode)."""
    allowed_strategies = ["mean", "median", "mode"]
    if strategy not in allowed_strategies:
        raise ValidationError(
            f"Nieznana strategia '{strategy}'. Wybierz jedną z: mean, median, mode."
        )

    validate_columns(session, columns)
    rows_before = len(session.current)

    new_frame = session.current.copy()
    filled_count = 0

    for column_name in columns:
        column = new_frame[column_name]
        missing_count = int(column.isna().sum())

        if missing_count == 0:
            continue

        if strategy in ["mean", "median"]:
            if not pd.api.types.is_numeric_dtype(column):
                raise ValidationError(
                    f"Strategia '{strategy}' wymaga kolumny liczbowej, a '{column_name}' "
                    "jest tekstowa. Wybierz 'mode' albo inną kolumnę."
                )
            if strategy == "mean":
                fill_value = column.mean()
            else:
                fill_value = column.median()
        else:
            modes = column.mode(dropna=True)
            if len(modes) == 0:
                raise ValidationError(
                    f"Kolumna '{column_name}' nie ma żadnych wartości, "
                    "więc nie da się wyliczyć wartości najczęstszej."
                )
            fill_value = modes.iloc[0]

        if pd.isna(fill_value):
            raise ValidationError(
                f"Kolumna '{column_name}' nie ma żadnych wartości, "
                "więc nie da się wyliczyć wartości zastępczej."
            )

        new_frame[column_name] = column.fillna(fill_value)
        filled_count += missing_count

    session.current = new_frame

    session.record(
        operation="fill_missing_with_statistic",
        params={"columns": columns, "strategy": strategy},
        rows_before=rows_before,
        affected=filled_count,
    )
    return filled_count

def find_out_of_range(session: DataSession,column_name: str,minimum: float | None,maximum: float | None) -> pd.Series:
    """Zwraca maskę true/false: które rekordy leżą poza zakresem"""
    validate_columns(session, [column_name])

    if minimum is None and maximum is None:
        raise ValidationError(
            "Nie podano żadnej granicy zakresu. Wpisz minimum, maksimum albo oba."
        )

    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValidationError(
            f"Minimum ({minimum}) jest większe niż maksimum ({maximum}). "
            "Zamień wartości miejscami."
        )

    column = session.current[column_name]
    if not pd.api.types.is_numeric_dtype(column):
        raise ValidationError(
            f"Kolumna '{column_name}' nie jest liczbowa, więc nie można sprawdzić zakresu. "
            "Wybierz kolumnę liczbową."
        )

    outside_mask = pd.Series(False, index=session.current.index)

    if minimum is not None:
        outside_mask = outside_mask | (column < minimum)

    if maximum is not None:
        outside_mask = outside_mask | (column > maximum)

    return outside_mask


def report_out_of_range(session: DataSession,column_name: str, minimum: float | None, maximum: float | None) -> int:
    """Liczy rekordy poza zakresem i zapisuje regułę w dzienniku"""
    outside_mask = find_out_of_range(session, column_name, minimum, maximum)
    found_count = int(outside_mask.sum())
    row_count = len(session.current)

    session.record(
        operation="check_range_rule",
        params={"column": column_name, "minimum": minimum, "maximum": maximum},
        rows_before=row_count,
        affected=0,
    )
    return found_count

def apply_range_rule(session: DataSession,column_name: str,minimum: float | None, maximum: float | None,action: str) -> int:
    """Stosuje decyzję użytkownika wobec wartości poza zakresem (to_missing albo drop_rows)."""
    allowed_actions = ["to_missing", "drop_rows"]
    if action not in allowed_actions:
        raise ValidationError(
            f"Nieznana akcja '{action}'. Wybierz jedną z: to_missing, drop_rows."
        )

    outside_mask = find_out_of_range(session, column_name, minimum, maximum)
    affected_count = int(outside_mask.sum())
    rows_before = len(session.current)

    new_frame = session.current.copy()

    if action == "to_missing":
        new_frame.loc[outside_mask, column_name] = float("nan")
    else:
        new_frame = new_frame[~outside_mask].copy()

    session.current = new_frame

    session.record(
        operation="apply_range_rule",
        params={
            "column": column_name,
            "minimum": minimum,
            "maximum": maximum,
            "action": action,
        },
        rows_before=rows_before,
        affected=affected_count,
    )
    return affected_count