"""Domain models for account synchronisation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SourceLiteral = Literal["excel", "quickbooks"]
ConflictReason = Literal["data_mismatch", "only_in_excel"]


@dataclass(slots=True)
class Account:
    """Represents an account synchronised between Excel and QuickBooks."""

    AccountType: str
    number: str
    name: str
    id: str
    source: SourceLiteral

    def __str__(self) -> str:
        """Return a string representation of the Account."""
        return f"Account(id={self.id}, name={self.name}, number={self.number}, type={self.AccountType}, source={self.source})\n"


@dataclass
class Conflict:
    """Represents a conflict between Excel and QuickBooks accounts."""

    excel_AccountType: str | None
    qb_AccountType: str | None
    record_id: str | None
    excel_number: str | None
    qb_number: str | None
    excel_name: str | None
    qb_name: str | None
    ConflictReason: str


@dataclass(slots=True)
class ComparisonReport:
    """Groups comparison outcomes for later processing."""

    added_chart_of_accounts: list[Account] = field(default_factory=list)
    qb_only: list[Account] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


__all__ = [
    "Account",
    "Conflict",
    "ComparisonReport",
    "ConflictReason",
    "SourceLiteral",
]
