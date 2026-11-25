"""Raport zmian i zapis oczyszczonych danych (na razie bez gui)"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from studio.errors import ValidationError
from studio.session import DataSession


def build_audit_report_text(session: DataSession) -> str:
    """Zwraca dziennik operacji jako tekst, jedna operacja w jednym wierszu."""
    lines = []
    lines.append("RAPORT ZMIAN")
    lines.append("=" * 40)

    if session.source_path is not None:
        lines.append(f"Plik źródłowy: {session.source_path}")

    lines.append(f"Rekordy w danych surowych: {len(session.raw)}")
    lines.append(f"Rekordy w danych bieżących: {len(session.current)}")
    lines.append("")

    if len(session.audit_log) == 0:
        lines.append("Nie wykonano żadnych operacji.")
    else:
        for number, entry in enumerate(session.audit_log, start=1):
            lines.append(f"{number}. {entry}")

    return "\n".join(lines)


def build_audit_table(session: DataSession) -> pd.DataFrame:
    """Zwraca dziennik operacji jako tabelę (do zapisu w CSV)."""
    rows = []

    for entry in session.audit_log:
        rows.append({
            "timestamp": entry.timestamp,
            "operation": entry.operation,
            "params": str(entry.params),
            "rows_before": entry.rows_before,
            "rows_after": entry.rows_after,
            "affected": entry.affected,
        })

    columns = ["timestamp", "operation", "params", "rows_before", "rows_after", "affected"]
    return pd.DataFrame(rows, columns=columns)


def save_audit_report(session: DataSession, path: Path | str) -> Path:
    """Zapisuje raport jako .txt albo .csv, zależnie od rozszerzenia."""
    path = Path(path)
    extension = path.suffix.lower()

    try:
        if extension == ".txt":
            path.write_text(build_audit_report_text(session), encoding="utf-8")
        elif extension == ".csv":
            build_audit_table(session).to_csv(path, index=False, encoding="utf-8")
        else:
            raise ValidationError(
                f"Nieobsługiwane rozszerzenie '{extension}'. Użyj .txt albo .csv."
            )
    except OSError as error:
        raise ValidationError(
            f"Nie można zapisać pliku {path} ({error}). "
            "Sprawdź uprawnienia i czy folder istnieje."
        ) from error

    return path


def save_cleaned_csv(session: DataSession, path: Path | str) -> Path:
    """Zapisuje dane bieżące do CSV (UTF-8, przecinek), bez kolumny indeksu."""
    path = Path(path)

    try:
        session.current.to_csv(path, index=False, encoding="utf-8")
    except OSError as error:
        raise ValidationError(
            f"Nie można zapisać pliku {path} ({error}). "
            "Sprawdź uprawnienia i czy folder istnieje."
        ) from error

    return path