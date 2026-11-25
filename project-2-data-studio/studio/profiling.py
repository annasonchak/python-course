"""Profil danych: rozmiar, typy, braki, unikalne wartości. Bez GUI."""
from __future__ import annotations

import pandas as pd


def get_shape(frame: pd.DataFrame) -> tuple[int, int]:
    """Zwraca (liczba rekordów, liczba kolumn)"""
    row_count = len(frame)
    column_count = len(frame.columns)
    return row_count, column_count

def build_column_profile(frame: pd.DataFrame) -> pd.DataFrame:
    """Zwraca tabelę: jeden wiersz na kolumnę, z typem, brakami i unikalnymi"""
    total_rows = len(frame)
    profile_rows = []

    for column_name in frame.columns:
        column = frame[column_name]

        missing_count = int(column.isna().sum())

        if total_rows > 0:
            missing_percent = round(missing_count / total_rows * 100, 2)
        else:
            missing_percent = 0.0

        profile_rows.append({
            "column": column_name,
            "dtype": str(column.dtype),
            "missing": missing_count,
            "missing_pct": missing_percent,
            "unique": int(column.nunique(dropna=True)),
        })

    return pd.DataFrame(profile_rows)

def count_exact_duplicates(frame: pd.DataFrame) -> int:
    """Zwraca liczbę rekordów, które są pełnymi duplikatami"""
    duplicate_flags = frame.duplicated(keep="first")
    return int(duplicate_flags.sum())


def build_numeric_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Zwraca statystyki opisowe tylko dla kolumn liczbowych"""
    numeric_columns = frame.select_dtypes(include="number")

    if len(numeric_columns.columns) == 0:
        return pd.DataFrame()

    statistics = numeric_columns.describe().transpose()
    statistics = statistics.reset_index()
    statistics = statistics.rename(columns={"index": "column"})
    return statistics