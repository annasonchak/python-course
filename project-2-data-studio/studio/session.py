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