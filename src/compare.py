"""Comparison helpers for account types."""

from __future__ import annotations

from typing import Dict, Iterable

from .models import ComparisonReport, Conflict, PaymentTerm


def compare_account_types(
    excel_terms: Iterable[PaymentTerm],
    qb_terms: Iterable[PaymentTerm],
) -> ComparisonReport:
    """Compare Excel and QuickBooks account types and identify discrepancies.

    This function reconciles account types from two sources (Excel and QuickBooks)
    by comparing their ``account_type`` field. Students must implement
    the logic to detect three types of discrepancies:

    1. Types that exist only in Excel
    2. Types that exist only in QuickBooks
    3. Types with matching ``account_type`` but different ``name`` values

    **Input Parameters:**

    :param excel_terms: An iterable of :class:`~payment_terms_cli.models.PaymentTerm`
        objects sourced from Excel. Each PaymentTerm has:

        - ``account_type`` (str): Unique identifier for the account type
        - ``name`` (str): Display name of the account type
        - ``source`` (SourceLiteral): Will be "excel" for these terms

        Example: ``PaymentTerm(account_type="EXPENSE", name="Expense", source="excel")``

    :param qb_terms: An iterable of :class:`~payment_terms_cli.models.PaymentTerm`
        objects sourced from QuickBooks. Structure is identical to ``excel_terms``
        but with ``source="quickbooks"``.

        Example: ``PaymentTerm(account_type="EXPENSE", name="Expenses", source="quickbooks")``

    **Return Value:**

    :return: A :class:`~payment_terms_cli.models.ComparisonReport` object containing
        three lists that categorize all discrepancies found:

        - ``excel_only`` (list[PaymentTerm]): Types with ``account_type`` values that
          appear in ``excel_terms`` but NOT in ``qb_terms``. These represent account
          types that need to be added to QuickBooks.

        - ``qb_only`` (list[PaymentTerm]): Types with ``account_type`` values that
          appear in ``qb_terms`` but NOT in ``excel_terms``. These represent account
          types that may need to be removed from QuickBooks or added to Excel.

        - ``conflicts`` (list[Conflict]): Types where the same ``account_type`` exists
          in both sources but the ``name`` field differs. Each
          :class:`~payment_terms_cli.models.Conflict` must have:

          - ``account_type`` (str): The shared account type
          - ``excel_name`` (str | None): The name from Excel
          - ``qb_name`` (str | None): The name from QuickBooks
          - ``reason`` (ConflictReason): Must be ``"name_mismatch"`` for these cases

    **Implementation Requirements:**

    1. Compare types based on their ``account_type`` field (case-sensitive)
    2. Build dictionaries or sets for efficient lookup of account types
    3. Identify types unique to each source (Excel-only and QB-only)
    4. For matching ``account_type`` values, compare the ``name`` fields
    5. If names differ, create a Conflict with reason ``"name_mismatch"``
    6. Return all findings in a ComparisonReport object

    **Example:**

    Given these inputs::

        excel_terms = [
            PaymentTerm(account_type="EXPENSE", name="Expense", source="excel"),
            PaymentTerm(account_type="INCOME", name="Income", source="excel"),
            PaymentTerm(account_type="ASSET", name="Asset", source="excel"),
        ]

        qb_terms = [
            PaymentTerm(account_type="EXPENSE", name="Expenses", source="quickbooks"),
            PaymentTerm(account_type="INCOME", name="Income", source="quickbooks"),
            PaymentTerm(account_type="LIABILITY", name="Liability", source="quickbooks"),
        ]

    Expected output::

        ComparisonReport(
            excel_only=[
                PaymentTerm(account_type="ASSET", name="Asset", source="excel")
            ],
            qb_only=[
                PaymentTerm(account_type="LIABILITY", name="Liability", source="quickbooks")
            ],
            conflicts=[
                Conflict(
                    account_type="EXPENSE",
                    excel_name="Expense",
                    qb_name="Expenses",
                    reason="name_mismatch"
                )
            ]
        )

    Note: INCOME appears in both sources with the same name, so it does not appear
    in any of the report's collections (no conflict, not Excel-only, not QB-only).
    """
    excel_dict: Dict[str, PaymentTerm] = {term.AccountType: term for term in excel_terms}
    qb_dict: Dict[str, PaymentTerm] = {term.AccountType: term for term in qb_terms}

    excel_only = [
        term for atype, term in excel_dict.items() if atype not in qb_dict
    ]
    qb_only = [
        term for atype, term in qb_dict.items() if atype not in excel_dict
    ]

    conflicts = []
    for atype in set(excel_dict.keys()).intersection(qb_dict.keys()):
        excel_name = excel_dict[atype].name
        qb_name = qb_dict[atype].name
        if excel_name != qb_name:
            conflicts.append(
                Conflict(
                    account_type=atype,  # Updated to reflect comparison of account types
                    excel_name=excel_name,
                    qb_name=qb_name,
                    reason="name_mismatch",
                )
            )

    return ComparisonReport(
        excel_only=excel_only,
        qb_only=qb_only,
        conflicts=conflicts,
    )


__all__ = ["compare_account_types"]