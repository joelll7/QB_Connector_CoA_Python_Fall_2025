"""High-level orchestration for the payment term CLI.

This module coordinates the end-to-end process of reading payment terms from
Excel, retrieving existing terms from QuickBooks, comparing both datasets,
creating any missing terms in QuickBooks, and writing a comprehensive JSON
report summarising the outcome.
"""

from __future__ import annotations

from pathlib import Path  # Filesystem path handling
from typing import Dict, List, Iterable  # Type annotations for clarity

from . import compare, excel_reader, qb_gateway  # Local modules used in orchestration
from .models import Conflict, Account  # Domain types
from .reporting import iso_timestamp, write_report  # JSON and timestamps

DEFAULT_REPORT_NAME = "payment_terms_report.json"  # Default output filename


def _account_to_dict(account: Account) -> Dict[str, str]:
    """Convert a Account object into a serialisable dict.

    This shape is used in the JSON report's "added_accounts" collection.
    """
    return {"id": account.id, "name": account.name, "number": account.number, "type": account.AccountType, "source": account.source}


def _conflict_to_dict(conflict: Conflict) -> Dict[str, object]:
    """Convert a Conflict object into a serialisable dict for the report."""
    return {
        "record_id": conflict.id,
        "excel_name": conflict.excel_name,
        "qb_name": conflict.qb_name,
        "excel_number": conflict.excel_number,
        "qb_number": conflict.qb_number,
        "excel_type": conflict.excel_AccountType,
        "qb_type": conflict.qb_AccountType,
        "reason": conflict.reason
    }


def _missing_in_excel_conflict(term: Account) -> Dict[str, object]:
    """Create a synthetic conflict for terms present only in QuickBooks.

    In the report, terms that exist in QuickBooks but not Excel are represented
    as conflicts with reason "missing_in_excel".
    """
    return {
        "record_id": term.id,
        "excel_name": None,
        "qb_name": term.name,
        "excel_number": None,
        "qb_number": term.number,
        "excel_type": None,
        "qb_type": term.AccountType,
        "reason": "missing_in_excel",
    }

def _count_matching_terms(
    excel_terms: List[Account], qb_terms: List[Account]
) -> int:
    """Return the number of terms that exist in both sources with identical data."""

    excel_by_id = {term.id: term for term in excel_terms}
    qb_by_id = {term.id: term for term in qb_terms}

    matches = 0
    for record_id in excel_by_id.keys() & qb_by_id.keys():
        excel_term = excel_by_id[record_id]
        qb_term = qb_by_id[record_id]
        if excel_term.name == qb_term.name and excel_term.number == qb_term.number and excel_term.AccountType == qb_term.AccountType:
            matches += 1
    return matches


def run_chart_of_accounts(
    company_file_path: str,
    workbook_path: str,
    *,
    output_path: str | None = None,
) -> Path:
    """Contract entry point for synchronising payment terms.

    Args:
        company_file_path: Path to the QuickBooks company file. Use an empty
            string to reuse the currently open company file.
        workbook_path: Path to the Excel workbook containing the
            payment_terms worksheet.
        output_path: Optional JSON output path. Defaults to
            payment_terms_report.json in the current working directory.

    Returns:
        Path to the generated JSON report.
    """
    # Choose report path: user-provided or default filename in CWD
    report_path = Path(output_path) if output_path else Path(DEFAULT_REPORT_NAME)
    # Initialise the report payload with default success shape
    report_payload: Dict[str, object] = {
        "status": "success",
        "generated_at": iso_timestamp(),
        "added_chart_of_accounts": [],
        "conflicts": [],
        "same_accounts": 0,
        "error": None,
    }

    try:
        # Extract terms from the Excel workbook
        excel_terms = excel_reader.extract_account(Path(workbook_path))
        # Fetch existing terms from QuickBooks
        qb_terms = qb_gateway.fetch_accounts(company_file_path)
        # Compare the two sources to find discrepancies
        comparison = compare.compare_accounts(excel_terms, qb_terms)

        # Add any terms that exist only in Excel to QuickBooks in a batch
        added_terms = qb_gateway.add_accounts_batch(
            company_file_path, comparison.excel_only
        )

        # Build conflicts list: name mismatches + items missing from Excel
        conflicts: List[Dict[str, object]] = []
        conflicts.extend(
            _conflict_to_dict(conflict) for conflict in comparison.conflicts
        )
        conflicts.extend(
            _missing_in_excel_conflict(term) for term in comparison.qb_only
        )

        # Populate the report payload with results
        report_payload["added_chart_of_accounts"] = [_account_to_dict(term) for term in added_terms]
        report_payload["conflicts"] = conflicts
        report_payload["same_accounts"] = _count_matching_terms(excel_terms, qb_terms)

    except Exception as exc:  # pragma: no cover - behaviour verified via tests
        # On any error, capture the message and mark the report as failure
        report_payload["status"] = "error"
        report_payload["error"] = str(exc)

    # Persist the report to disk and return its path
    write_report(report_payload, report_path)
    return report_path


__all__ = ["run_chart_of_accounts",  "DEFAULT_REPORT_NAME"]
