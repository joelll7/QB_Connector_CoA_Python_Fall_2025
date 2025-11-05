"""Tests for Excel processing functions.

This module tests the core Excel processing functionality and payment terms import.
"""

import tempfile
from pathlib import Path

import pytest
from openpyxl import Workbook

from src.excel_reader import extract_account


def create_test_excel(file_path: Path) -> None:
    """Create a test Excel file with account data."""

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "chartofaccount"

    # Add headers
    sheet.append(["ID", "Number", "Name", "Type"])

    # Add test data
    sheet.append([1, 101, "Materials", "Cost of Goods Sold"])
    sheet.append([2, 102, "Office Supplies", "Expense"])

    workbook.save(file_path)


def test_extract_account() -> None:
    """Test the extract_account function."""
    with pytest.raises(FileNotFoundError):
        extract_account(Path("nonexistent.xlsx"))

    # Create a temporary Excel file

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        create_test_excel(tmp_path)

        # Extract accounts
        accounts = extract_account(tmp_path)

        # Assertions
        assert len(accounts) == 2

        assert accounts[0].id == "1"
        assert accounts[0].number == "101"
        assert accounts[0].name == "Materials"
        assert accounts[0].AccountType == "Cost of Goods Sold"
        assert accounts[0].source == "excel"

        assert accounts[1].id == "2"
        assert accounts[1].number == "102"
        assert accounts[1].name == "Office Supplies"
        assert accounts[1].AccountType == "Expense"
        assert accounts[1].source == "excel"
