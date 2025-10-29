"""Domain models for payment term synchronisation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


SourceLiteral = Literal["excel", "quickbooks"]
ConflictReason = Literal["name_mismatch", "missing_in_excel", "missing_in_quickbooks"]


@dataclass(slots=True)
class Account:
    """Represents an account synchronised between Excel and QuickBooks."""

    AccountType: str
    number: int
    name: str
    id: str
    source: SourceLiteral


@dataclass(slots=True)
class Conflict:
    """Describes a discrepancy between Excel and QuickBooks accounts."""

    AccountType: str
    excel_name: str | None
    qb_name: str | None
    id: str
    reason: ConflictReason


@dataclass(slots=True)
class ComparisonReport:
    """Groups comparison outcomes for later processing."""

    excel_only: list[Account] = field(default_factory=list)
    qb_only: list[Account] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)


__all__ = [
    "Account",
    "Conflict",
    "ComparisonReport",
    "ConflictReason",
    "SourceLiteral",
]