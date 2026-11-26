"""Wykresy"""
from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure

from studio.errors import ValidationError
from studio.session import DataSession


def get_numeric_values(session: DataSession, column_name: str) -> pd.Series:
    """Zwraca wartości liczbowe kolumny bez braków albo zgłasza ValidationError."""
    if column_name not in session.current.columns:
        raise ValidationError(
            f"Kolumna '{column_name}' nie istnieje w danych. Wybierz kolumnę z listy."
        )

    column = session.current[column_name]

    if not pd.api.types.is_numeric_dtype(column):
        raise ValidationError(
            f"Kolumna '{column_name}' nie jest liczbowa, więc nie można narysować tego wykresu. "
            "Wybierz kolumnę liczbową."
        )

    values = column.dropna()

    if len(values) == 0:
        raise ValidationError(
            f"Kolumna '{column_name}' nie zawiera żadnych wartości. Wybierz inną kolumnę."
        )

    if values.nunique() < 2:
        raise ValidationError(
            f"Kolumna '{column_name}' jest stała (wszystkie wartości są takie same), "
            "więc wykres nic nie pokaże. Wybierz kolumnę z różnymi wartościami."
        )

    return values


def histogram_figure(session: DataSession, column_name: str) -> Figure:
    """Histogram rozkładu jednej kolumny liczbowej."""
    values = get_numeric_values(session, column_name)

    figure = Figure(figsize=(7, 4), dpi=100)
    axes = figure.add_subplot(1, 1, 1)
    axes.hist(values, bins="auto", edgecolor="white")
    axes.set_title(f"Histogram: {column_name}")
    axes.set_xlabel(column_name)
    axes.set_ylabel("Liczba rekordów")
    figure.tight_layout()
    return figure


def box_plot_figure(session: DataSession, column_name: str) -> Figure:
    """Wykres pudełkowy jednej kolumny liczbowej (widać medianę, kwartyle i odstające)."""
    values = get_numeric_values(session, column_name)

    figure = Figure(figsize=(5, 5), dpi=100)
    axes = figure.add_subplot(1, 1, 1)
    axes.boxplot(values)
    axes.set_xticks([1])
    axes.set_xticklabels([column_name])
    axes.set_title(f"Wykres pudełkowy: {column_name}")
    axes.set_xlabel("Kolumna")
    axes.set_ylabel(column_name)
    figure.tight_layout()
    return figure