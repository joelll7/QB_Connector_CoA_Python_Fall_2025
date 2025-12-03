"""Comparison helpers for account types."""

from __future__ import annotations

from typing import Dict, Iterable

from src.models import ComparisonReport
from src.models import Conflict
from src.models import Account


def compare_accounts(
    excel_accounts: Iterable[Account],
    qb_accounts: Iterable[Account],
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
            conflicts=[id= "2",
                       excel_AccountType="EXPENSE", qb_AccountType="EXPENSE",
                       excel_name="Expense", qb_name="Expenses",
                       excel_number="2000", qb_number="2000",
                       reason="data_mismatch"]
        )

    Note: INCOME appears in both sources with the same data, so it does not appear
    in any of the report's collections (no conflict, not Excel-only, not QB-only).
    """
    excel_dict: Dict[str, Account] = {account.id: account for account in excel_accounts}
    qb_dict: Dict[str, Account] = {account.id: account for account in qb_accounts}

    added_chart_of_accounts = [
        account for aID, account in excel_dict.items() if aID not in qb_dict
    ]

    qb_only = [account for aID, account in qb_dict.items() if aID not in excel_dict]

    conflicts = []
    for aID in set(excel_dict.keys()).intersection(qb_dict.keys()):
        excel_name = excel_dict[aID].name
        qb_name = qb_dict[aID].name
        excel_number = excel_dict[aID].number
        qb_number = qb_dict[aID].number
        excel_atype = excel_dict[aID].AccountType
        qb_atype = qb_dict[aID].AccountType
        if (
            excel_name != qb_name
            or excel_number != qb_number
            or excel_atype != qb_atype
        ):
            conflicts.append(
                Conflict(
                    record_id=aID,  # Updated to reflect comparison of account types
                    excel_name=excel_name,
                    qb_name=qb_name,
                    excel_number=excel_number,
                    qb_number=qb_number,
                    excel_AccountType=excel_atype,
                    qb_AccountType=qb_atype,
                    ConflictReason="data_mismatch",
                )
            )

    return ComparisonReport(
        added_chart_of_accounts=added_chart_of_accounts,
        qb_only=qb_only,
        conflicts=conflicts,
    )


__all__ = ["compare_accounts"]
