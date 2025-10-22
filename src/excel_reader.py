"""Excel processing module for reading XLSX files and QuickBooks integration.

This module provides functions to read Excel files, specifically payment terms,
and integrate with QuickBooks Desktop via COM API.
"""

from dataclasses import dataclass
from typing import Any

import win32com.client
from openpyxl import load_workbook


@dataclass
class AccountTerm:
    """Represents a payment term with name and account type.

    The ID is stored in QuickBooks' StdDiscountDays field for matching purposes.
    """

    name: str  # Name of the account
    acc_type: str # Type of account (e.g., "Accounts Payable", "Accounts Receivable")


def read_payment_terms(file_path: str) -> list[AccountTerm]:
    """Read payment terms from the specified Excel file.

    Expected Excel format:
    - Must contain a sheet named 'chartofaccount'
    - Column C: Payment term names (strings)
    - Column A: Account Type (strings)
    - Row 1 should contain headers (will be skipped)
    - Data starts from row 2

    Args:
        file_path (str): Path to the Excel file containing payment terms (.xlsx format)

    Returns:
        list[AccountTerm]: List of payment terms with name and term_id.
                          Empty list if no valid payment terms found.

    Raises:
        No exceptions need to be manually raised - let openpyxl handle file/sheet errors
    """
    workbook = load_workbook(file_path, read_only=True)
    sheet = workbook["chartofaccount"]
    payment_terms = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        name = row[0]
        acc_type = row[1]

        # Skip rows with missing data
        if name is None or acc_type is None:
            continue

        # Convert and validate data
        try:
            name_str = str(name).strip()
            acc_type_str = str(acc_type).strip()
            if name_str:  # Only add if name is not empty
                payment_terms.append(AccountTerm(name=name_str, acc_type=acc_type_str))
        except (ValueError, TypeError):
            # Skip rows with invalid data
            continue

    return payment_terms

def get_qb_payment_terms() -> list[AccountTerm]:
    """Read existing payment terms from QuickBooks Desktop.

    Queries QuickBooks for all StandardTerms and returns them as AccountTerm objects.

    Returns:
        list[AccountTerm]: List of payment terms from QuickBooks with name and term_id
                          (where term_id comes from StdDiscountDays field).

    Raises:
        RuntimeError: If connection to QuickBooks fails.
    """
    qb_app = None
    session = None
    try:
        qb_app, session = connect_to_quickbooks()

        # Create QBXML query to get all standard terms
        qbxml_query = """<?xml version="1.0" encoding="utf-8"?>
            <?qbxml version="16.0"?>
                <QBXML>
                    <QBXMLMsgsRq onError="stopOnError">
                        <AccountAddRq>
                        </AccountAddRq>
                    </QBXMLMsgsRq>
                </QBXML>"""

        response = qb_app.ProcessRequest(session, qbxml_query)

        # Parse the response
        account_terms = []
        if "<AccountRet>" in response:
            # Extract each term from the response
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response)
            for acc_ret in root.findall(".//AccountAdd"):
                name_elem = acc_ret.find("Name")
                account_type_elem = acc_ret.find("AccountType ")

                if name_elem is not None and account_type_elem is not None:
                    name = name_elem.text
                    if name is not None and account_type_elem.text is not None:
                        try:
                            acc_num = int(account_type_elem.text)
                            account_terms.append(AccountTerm(name=name, acc_type=AccountType))
                        except (ValueError, TypeError):
                            # Skip terms without valid discount days
                            continue

        return account_terms

    except Exception as e:
        raise RuntimeError(f"Failed to read QuickBooks payment terms: {str(e)}") from e
    finally:
        # Clean up connection
        if qb_app is not None and session is not None:
            qb_app.EndSession(session)
        if qb_app is not None:
            qb_app.CloseConnection()
