"""QuickBooks COM gateway helpers for payment terms."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from contextlib import contextmanager
from typing import Iterator, List

try:
    import win32com.client  # type: ignore
except ImportError:  # pragma: no cover
    win32com = None  # type: ignore

from models import Account


APP_NAME = "Quickbooks Connector" # do not chanege this


def _require_win32com() -> None:
    if win32com is None:  # pragma: no cover - exercised via tests
        raise RuntimeError("pywin32 is required to communicate with QuickBooks")


@contextmanager
def _qb_session() -> Iterator[tuple[object, object]]:
    _require_win32com()
    session = win32com.client.Dispatch("QBXMLRP2.RequestProcessor")
    session.OpenConnection2("", APP_NAME, 1)
    ticket = session.BeginSession("", 0)
    try:
        yield session, ticket
    finally:
        try:
            session.EndSession(ticket)
        finally:
            session.CloseConnection()


def _send_qbxml(qbxml: str) -> ET.Element:
    with _qb_session() as (session, ticket):
        #print(f"Sending QBXML:\n{qbxml}")  # Debug output
        raw_response = session.ProcessRequest(ticket, qbxml)  # type: ignore[attr-defined]
        #print(f"Received response:\n{raw_response}")  # Debug output
    return _parse_response(raw_response)


def _parse_response(raw_xml: str) -> ET.Element:
    root = ET.fromstring(raw_xml)
    response = root.find(".//*[@statusCode]")
    if response is None:
        raise RuntimeError("QuickBooks response missing status information")

    status_code = int(response.get("statusCode", "0"))
    status_message = response.get("statusMessage", "")
    # Status code 1 means "no matching objects found" - this is OK for queries
    if status_code != 0 and status_code != 1:
        print(f"QuickBooks error ({status_code}): {status_message}")
        raise RuntimeError(status_message)
    return root


def fetch_chart_of_accounts(company_file: str | None = None) -> List[Account]:
    """Return accounts in Chart of Accounts currently stored in QuickBooks."""

    qbxml = (
        '<?xml version="1.0"?>\n'
        '<?qbxml version="16.0"?>\n'
        "<QBXML>\n"
        '  <QBXMLMsgsRq onError="stopOnError">\n'
        "    <AccountQueryRq/>\n"
        "  </QBXMLMsgsRq>\n"
        "</QBXML>"
    )
    root = _send_qbxml(qbxml)
    terms: List[Account] = []
    for account_ret in root.findall(".//AccountRet"):
        id = (account_ret.findtext("Desc") or "")
        name = (account_ret.findtext("Name") or "")
        acc_number = (account_ret.findtext("AccountNumber") or "")
        acc_type = (account_ret.findtext("AccountType") or "")

        if not id:
            continue
        try:
            id = str(int(id))
        except ValueError:
            id = id.strip()
        if not id:
            continue

        terms.append(Account(id=id, name=name, number=acc_number, AccountType=acc_type, source="quickbooks"))

    return terms


def add_accounts_batch(
    company_file: str | None, terms: List[Account]
) -> List[Account]:
    """Create multiple payment terms in QuickBooks in a single batch request."""

    if not terms:
        return []

    # Build the QBXML with multiple StandardTermsAddRq entries
    requests = []
    for term in terms:
        try:
            desc_value = int(term.id)
        except ValueError as exc:
            raise ValueError(
                f"id must be numeric for QuickBooks account terms: {term.id}"
            ) from exc

        requests.append(
            f"    <AccountAddRq>\n"
            f"      <AccountAdd>\n"
            f"        <Name>{_escape_xml(term.name)}</Name>\n"
            f"        <AccountType>{_escape_xml(term.AccountType)}</AccountType>\n" #UNSURE ABOUT THIS
            f"        <AccountNumber>{_escape_xml(term.number)}</AccountNumber>\n"
            f"        <Desc>{desc_value}</Desc>\n"
            f"      </AccountAdd>\n"
            f"    </AccountAddRq>"
        )

    qbxml = (
        '<?xml version="1.0"?>\n'
        '<?qbxml version="13.0"?>\n'
        "<QBXML>\n"
        '  <QBXMLMsgsRq onError="continueOnError">\n' + "\n".join(requests) + "\n"
        "  </QBXMLMsgsRq>\n"
        "</QBXML>"
    )

    try:
        root = _send_qbxml(qbxml)
    except RuntimeError as exc:
        # If the entire batch fails, return empty list
        print(f"Batch add failed: {exc}")
        return []

    # Parse all responses
    added_accounts: List[Account] = []
    for account_ret in root.findall(".//AccountRet"):
        id = account_ret.findtext("Desc").strip()
        if not id:
            continue
        try:
            id = str(int(id))
        except ValueError:
            id = id.strip()
        name = (account_ret.findtext("Name") or "").strip()
        acc_number = (account_ret.findtext("AccountNumber") or "").strip()
        acc_type = (account_ret.findtext("AccountType") or "").strip()
        added_accounts.append(
            Account(id=id, name=name, acc_number=acc_number, acc_type=acc_type, source="quickbooks")
        )

    return added_accounts


def add_account(company_file: str | None, term: Account) -> Account:
    """Create an account in QuickBooks and return the stored record."""

    try:
        desc_value = int(term.id)
    except ValueError as exc:
        raise ValueError(
            "id must be numeric for QuickBooks account"
        ) from exc

    qbxml = (
        '<?xml version="1.0"?>\n'
        '<?qbxml version="13.0"?>\n'
        "<QBXML>\n"
        '  <QBXMLMsgsRq onError="stopOnError">\n'
        "    <AccountAddRq>\n"
        "      <AccountAdd>\n"
        f"        <Name>{_escape_xml(term.name)}</Name>\n"
        f"        <AccountType>{_escape_xml(term.AccountType)}</AccountType>\n" #UNSURE ABOUT THIS
        f"        <AccountNumber>{_escape_xml(term.number)}</AccountNumber>\n"
        f"        <Desc>{desc_value}</Desc>\n"
        "      </AccountAdd>\n"
        "    </AccountAddRq>\n"
        "  </QBXMLMsgsRq>\n"
        "</QBXML>"
    )

    try:
        root = _send_qbxml(qbxml)
    except RuntimeError as exc:
        # Check if error is "name already in use" (error code 3100)
        if "already in use" in str(exc):
            # Return the term as-is since it already exists
            return Account(
                id=term.id, name=term.name, acc_type=term.AccountType, acc_number=term.acc_number, source="quickbooks"
            )
        raise

    account_ret = root.find(".//AccountRet")
    if account_ret is None:
        return Account(
            record_id=term.id, name=term.name, acc_type=term.AccountType, acc_number=term.acc_number, source="quickbooks"
        )

    id = account_ret.findtext("Desc") or term.id
    try:
        record_id = str(int(id))
    except ValueError:
        id = id.strip()
    name = (account_ret.findtext("Name") or term.name).strip()
    acc_number = (account_ret.findtext("AccountNumber") or term.number).strip()
    acc_type = (account_ret.findtext("AccountType") or term.AccountType).strip()

    return Account(id=id, name=name, acc_type=acc_type, acc_number=acc_number, source="quickbooks")


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


__all__ = ["fetch_accounts", "add_account", "add_accounts_batch"]

if __name__ == "__main__":  # pragma: no cover - manual invocation
    import sys
    
    # Allow running as a script: poetry run python payment_terms_cli/excel_reader.py
    try:
        qb_accounts = fetch_chart_of_accounts("")
        for acc in qb_accounts:
            print(acc)
    except Exception as e:
        print(f"Error: {e}")
        print("Usage: python payment_terms_cli/excel_reader.py <path-to-workbook.xlsx>")
        sys.exit(1)