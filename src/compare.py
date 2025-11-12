"""Comparison helpers for account types."""

from __future__ import annotations

from typing import Dict, Iterable

from .models import ComparisonReport, Conflict, Account


def compare_account_types(
    excel_terms: Iterable[Account],
    qb_terms: Iterable[Account],
) -> ComparisonReport:
    """Compare Excel and QuickBooks accounts and identify discrepancies.

    This function reconciles accounts from two sources (Excel and QuickBooks)
    by comparing their ``id`` field. Students must implement
    the logic to detect three types of discrepancies:

    1. Accounts that exist only in Excel
    2. Accounts that exist only in QuickBooks
    3. Accounts with matching ``id`` but different ``name`` and/or ``number`` and/or ``AccountType`` values

    **Input Parameters:**

    :param excel_terms: An iterable of :class:`~src.models.Account`
        objects sourced from Excel. Each Account has:

        - ``AccountType`` (str): account type identifier
        - ``id`` (str): Unique identifier of the account
        - ``name`` (str): Display name of the account type
        - ``number`` (str): Account number
        - ``source`` (SourceLiteral): Will be "excel" for these terms

        Example: ``Account(AccountType="Other Expense", id="101" name="Expense", number="123", source="excel")``

    :param qb_accounts: An iterable of :class:`~src.models.Account`
        objects sourced from QuickBooks. Structure is identical to ``excel_accounts``
        but with ``source="quickbooks"``.

        Example: ``Account(AccountType="Other Expense", id="101" name="Expense", number="123", source="quickbooks")``

    **Return Value:**

    :return: A :class:`~src.models.ComparisonReport` object containing
        three lists that categorize all discrepancies found:

        - ``excel_only`` (list[PaymentTerm]): Types with ``account_type`` values that
          appear in ``excel_terms`` but NOT in ``qb_terms``. These represent account
          types that need to be added to QuickBooks.

        - ``qb_only`` (list[PaymentTerm]): Types with ``account_type`` values that
          appear in ``qb_terms`` but NOT in ``excel_terms``. These represent account
          types that may need to be removed from QuickBooks or added to Excel.

        - ``conflicts`` (list[Conflict]): Types where the same ``id`` exists
          in both sources but the ``name`` and/or ``number`` and/or ``AccountType`` 
          field differs. Each :class:`~src.models.Conflict` must have:

          - id: str Identifier of the account type with the conflict

          - excel_AccountType: str - The account type from Excel
          - qb_AccountType: str - The account type from QuickBooks

          - excel_name: str | None - The name from Excel
          - qb_name: str | None - The name from QuickBooks

          - excel_number: str | None - The number from Excel
          - qb_number: str | None - The number from QuickBooks

         reason: ConflictReason - Set to "data_mismatch" to indicate differing data

    **Implementation Requirements:**

    1. Compare types based on their ``id`` field (case-sensitive)
    2. Build dictionaries or sets for efficient lookup of account types
    3. Identify ids unique to each source (Excel-only and QB-only)
    4. For matching ``id`` values, compare the ``name``, ``number``, and ``AccountType`` fields
    5. If any fields differ, create a Conflict with reason ``"data_mismatch"``
    6. Return all findings in a ComparisonReport object

    **Example:**

    Given these inputs::

        excel_terms = [
            Account(AccountType="ASSET", id="1", name="Asset", number="1000", source="excel"),
            Account(AccountType="EXPENSE", id="2", name="Expense", number="2000", source="excel"),
            Account(AccountType="INCOME", id="3", name="Income", number="3000", source="excel"),
        ]

        qb_terms = [
            Account(AccountType="LIABILITY", id="4", name="Liability", number="4000", source="quickbooks"),
            Account(AccountType="EXPENSE", id="2", name="Expenses", number="2000", source="quickbooks"),
            Account(AccountType="INCOME", id="3", name="Income", number="3000", source="quickbooks"),
        ]

    Expected output::

        ComparisonReport(
            excel_only=[Account(AccountType="ASSET", id="1", name="Asset", number="1000", source="excel")],
            qb_only=[Account(AccountType="LIABILITY", id="4", name="Liability", number="4000", source="quickbooks")],
            conflicts=[AccountType="EXPENSE", id="2", excel_name="Expense", qb_name="Expenses", reason="data_mismatch"]
        )

    Note: INCOME appears in both sources with the same name, so it does not appear
    in any of the report's collections (no conflict, not Excel-only, not QB-only).
    """
    excel_dict: Dict[str, Account] = {term.AccountType: term for term in excel_terms}
    qb_dict: Dict[str, Account] = {term.AccountType: term for term in qb_terms}

    excel_only = [term for atype, term in excel_dict.items() if atype not in qb_dict]
    qb_only = [term for atype, term in qb_dict.items() if atype not in excel_dict]

    conflicts = []
    for atype in set(excel_dict.keys()).intersection(qb_dict.keys()):
        excel_name = excel_dict[atype].name
        qb_name = qb_dict[atype].name
        if excel_name != qb_name:
            conflicts.append(
                Conflict(
                    AccountType=atype,  # Updated to reflect comparison of account types
                    id=excel_dict[atype].id,
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
