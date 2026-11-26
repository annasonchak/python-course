"""Wykresy"""
from __future__ import annotations

import pandas as pd
import seaborn as sns
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

MAX_BAR_CATEGORIES = 20


def scatter_figure(session: DataSession, x_column: str, y_column: str) -> Figure:
    """Wykres punktowy dwóch różnych kolumn liczbowych."""
    if x_column == y_column:
        raise ValidationError(
            "Wybrano tę samą kolumnę dla obu osi. Wybierz dwie różne kolumny."
        )

    # Walidacja każdej kolumny osobno (typ, brak wartości, stałość)
    get_numeric_values(session, x_column)
    get_numeric_values(session, y_column)

    pair = session.current[[x_column, y_column]].dropna()

    figure = Figure(figsize=(7, 5), dpi=100)
    axes = figure.add_subplot(1, 1, 1)
    axes.scatter(pair[x_column], pair[y_column], alpha=0.6)
    axes.set_title(f"Wykres punktowy: {y_column} względem {x_column}")
    axes.set_xlabel(x_column)
    axes.set_ylabel(y_column)
    figure.text(
        0.5, 0.01,
        "Uwaga: korelacja nie oznacza przyczynowości.",
        ha="center", fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    return figure


def bar_figure(session: DataSession, column_name: str) -> Figure:
    """Wykres słupkowy liczby rekordów w każdej kategorii."""
    if column_name not in session.current.columns:
        raise ValidationError(
            f"Kolumna '{column_name}' nie istnieje w danych. Wybierz kolumnę z listy."
        )

    column = session.current[column_name]

    if pd.api.types.is_numeric_dtype(column):
        raise ValidationError(
            f"Kolumna '{column_name}' jest liczbowa. Wykres słupkowy wymaga kolumny "
            "kategorialnej (tekstowej). Dla liczb użyj histogramu."
        )

    counts = column.dropna().value_counts()

    if len(counts) == 0:
        raise ValidationError(
            f"Kolumna '{column_name}' nie zawiera żadnych wartości. Wybierz inną kolumnę."
        )

    if len(counts) > MAX_BAR_CATEGORIES:
        raise ValidationError(
            f"Kolumna '{column_name}' ma {len(counts)} kategorii, a limit to "
            f"{MAX_BAR_CATEGORIES}. Wybierz kolumnę z mniejszą liczbą kategorii."
        )

    figure = Figure(figsize=(7, 4), dpi=100)
    axes = figure.add_subplot(1, 1, 1)
    axes.bar([str(name) for name in counts.index], counts.values, edgecolor="white")
    axes.set_title(f"Liczba rekordów w kategoriach: {column_name}")
    axes.set_xlabel(column_name)
    axes.set_ylabel("Liczba rekordów")
    figure.tight_layout()
    return figure

def get_correlation_matrix(session: DataSession) -> pd.DataFrame:
    """Zwraca macierz korelacji Pearsona dla kolumn liczbowych (bez stałych)."""
    numeric_frame = session.current.select_dtypes(include="number")

    usable_columns = []
    for column_name in numeric_frame.columns:
        if numeric_frame[column_name].nunique(dropna=True) >= 2:
            usable_columns.append(column_name)

    if len(usable_columns) < 2:
        raise ValidationError(
            "Do korelacji potrzebne są co najmniej dwie liczbowe kolumny, "
            "które nie są stałe. Wczytaj plik z większą liczbą kolumn liczbowych."
        )

    return numeric_frame[usable_columns].corr()


def correlation_figure(session: DataSession) -> Figure:
    """Mapa cieplna korelacji między kolumnami liczbowymi."""
    matrix = get_correlation_matrix(session)
    size = len(matrix.columns)

    figure = Figure(figsize=(max(6, size * 0.9), max(5, size * 0.8)), dpi=100)
    axes = figure.add_subplot(1, 1, 1)
    sns.heatmap(
        matrix,
        ax=axes,
        annot=True,
        fmt=".2f",
        vmin=-1,
        vmax=1,
        cmap="coolwarm",
    )
    axes.set_title("Macierz korelacji (Pearson)")
    axes.set_xlabel("Kolumna")
    axes.set_ylabel("Kolumna")
    figure.text(
        0.5, 0.01,
        "Uwaga: korelacja nie oznacza przyczynowości.",
        ha="center", fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    return figure