"""High-level orchestration for the payment term CLI."""

from __future__ import annotations

from pathlib import Path

from . import compare, excel_reader, qb_gateway
from .models import Account, Conflict
from .reporting import iso_timestamp, write_report

DEFAULT_REPORT_NAME = "chart_of_accounts_report.json"


def _account_to_dict(account: Account) -> dict[str, str, str, str]:
    return {"id": account.id, "name": account.name, "type": account.type, "number": account.number, "source": account.source}


def _conflict_to_dict(conflict: Conflict) -> dict[str, object]:
    return {
        "record_id": conflict.id,
        "excel_name": conflict.excel_name,
        "qb_name": conflict.qb_name,
        "reason": conflict.reason,
    }


def _missing_in_excel_conflict(account: Account) -> dict[str, object]:
    return {
        "record_id": account.id,
        "excel_name": None,
        "qb_name": account.name,
        "reason": "missing_in_excel",
    }


def run_accounts(
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
    report_path = Path(output_path) if output_path else Path(DEFAULT_REPORT_NAME)
    report_payload: dict[str, object] = {
        "status": "success",
        "generated_at": iso_timestamp(),
        "added_terms": [],
        "conflicts": [],
        "error": None,
    }

    # !!!!
    #vvvvvvvvvvvvvvvvvvvvvvvvvvv MUST BE UPDATED vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    # !!!!

    try:
        excel_accounts = excel_reader.extract_accounts(Path(workbook_path))
        qb_accounts = qb_gateway.fetch_accounts(company_file_path)
        comparison = compare.compare_payment_terms(excel_accounts, qb_accounts)

        added_accounts = qb_gateway.add_accounts_batch(
            company_file_path, comparison.excel_only
        )

        conflicts: list[dict[str, object]] = []
        conflicts.extend(
            _conflict_to_dict(conflict) for conflict in comparison.conflicts
        )
        conflicts.extend(
            _missing_in_excel_conflict(term) for term in comparison.qb_only
        )

        report_payload["added_accounts"] = [_account_to_dict(account) for account in added_accounts]
        report_payload["conflicts"] = conflicts

    except Exception as exc:  # pragma: no cover - behaviour verified via tests
        report_payload["status"] = "error"
        report_payload["error"] = str(exc)

    write_report(report_payload, report_path)
    return report_path


__all__ = ["run_accounts", "DEFAULT_REPORT_NAME"]
