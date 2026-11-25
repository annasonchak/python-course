"""Model sesji: dane surowe, dane bieżące i dziennik operacji"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from studio.errors import DataLoadError

@dataclass(frozen=True)
class AuditEntry:
    """Jeden wpis w dzienniku zmian"""

    operation: str
    params: dict[str, Any]
    rows_before: int
    rows_after: int
    affected: int
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def __str__(self) -> str:
        return (
            f"[{self.timestamp}] {self.operation} {self.params} | "
            f"rekordy: {self.rows_before} -> {self.rows_after} | "
            f"dotknięte: {self.affected}"
        )

SEPARATORS = (",", ";", "\t")
ENCODINGS = ("utf-8-sig", "cp1250")

def detect_separator(text: str) -> str:
    """Wybiera separator, który najczęściej występuje w nagłówku"""
    lines = text.splitlines()

    header = ""
    if len(lines) > 0:
        header = lines[0]

    best_separator = ","
    best_count = 0

    for separator in SEPARATORS:
        count = header.count(separator)
        if count > best_count:
            best_count = count
            best_separator = separator

    return best_separator


def read_text_with_fallback(path: Path) -> str:
    """Próbuje odczytać plik w kilku kodowaniach po kolei"""
    for encoding in ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise DataLoadError(
        "Nie można odczytać kodowania pliku. "
        "Zapisz plik jako CSV UTF-8 i spróbuj ponownie."
    )

@dataclass
class DataSession:
    """Przechowuje dane surowe (nigdy nie zmieniane) i dane bieżące (czyszczone)"""

    raw: pd.DataFrame
    current: pd.DataFrame = field(init=False)
    audit_log: list[AuditEntry] = field(default_factory=list)
    source_path: Path | None = None

    def __post_init__(self) -> None:
        self.current = self.raw.copy(deep=True)

    @classmethod
    def from_csv(cls, path: Path | str, separator: str | None = None) -> DataSession:
        path = Path(path)
        if not path.is_file():
            raise DataLoadError(f"Plik nie istnieje: {path}, wybierz inny plik")

        text = read_text_with_fallback(path)
        if text.strip() == "":
            raise DataLoadError("Plik jest pusty, wybierz plik z nagłówkiem i danymi")

        if separator is None:
            chosen_separator = detect_separator(text)
        else:
            chosen_separator = separator

        try:
            frame = pd.read_csv(io.StringIO(text), sep=chosen_separator)
        except pd.errors.ParserError as error:
            raise DataLoadError(
                f"Wadliwy wiersz w pliku ({error}), sprawdź separator i cudzysłowy"
            ) from error

        if frame.empty:
            raise DataLoadError("Plik nie zawiera rekordów (tylko nagłówek)")

        session = cls(frame)
        session.source_path = path
        return session

    def record(self, operation: str, params: dict[str, Any], rows_before: int, affected: int) -> AuditEntry:
        """Dopisuje wpis do dziennika"""
        entry = AuditEntry(operation, params, rows_before, len(self.current), affected)
        self.audit_log.append(entry)
        return entry

    def reset(self) -> None:
        """Wraca do danych surowych, ale dziennik zostaje, tylko + reset"""
        rows_before = len(self.current)
        self.current = self.raw.copy(deep=True)
        self.record("reset", {}, rows_before, abs(rows_before - len(self.current)))

