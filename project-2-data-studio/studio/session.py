"""Model sesji: dane surowe, dane bieżące i dziennik operacji"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

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

@dataclass
class DataSession:
    """Przechowuje dane surowe (nigdy nie zmieniane) i dane bieżące (czyszczone)"""

    raw: pd.DataFrame
    current: pd.DataFrame = field(init=False)
    audit_log: list[AuditEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current = self.raw.copy(deep=True)

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

