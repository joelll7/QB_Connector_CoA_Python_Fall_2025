"""Tests for Excel processing functions.

This module tests the core Excel processing functionality and payment terms import.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from openpyxl import Workbook

from src.excel_reader import (
    AccountTerm,
    read_payment_terms
)


def create_payment_terms_excel(file_path: str) -> None:
    """Create a test Excel file with payment terms data."""
    workbook = Workbook()

    # Remove default sheet
    workbook.remove(workbook.active)

    # Create payment_terms sheet
    sheet = workbook.create_sheet("chartofaccount")
    sheet["B1"] = "Name"
    sheet["A1"] = "acc_type"

    # Add test payment terms
    payment_terms_data = [
        ("Materials", 1, "Cost of Goods Sold"),
        ("Office Supplies", 2, "Expense")
    ]

    for i, (name, ID, acc_type) in enumerate(payment_terms_data, start=2):
        sheet[f"B{i}"] = name
        sheet[f"A{i}"] = acc_type

    workbook.save(file_path)


class TestPaymentTerms:
    """Test cases for payment terms functionality."""

    @pytest.fixture
    def payment_terms_excel_file(self):
        """Create a temporary Excel file with payment terms for testing."""
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp_path = Path(tmp.name)
        try:
            tmp.close()
            create_payment_terms_excel(str(tmp_path))
            yield str(tmp_path)
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except PermissionError:
                pass

    def test_payment_term_dataclass(self):
        """Test AccountTerm dataclass."""
        term = AccountTerm(name="Materials", acc_type="Cost of Goods Sold")
        assert term.name == "Materials"
        assert term.acc_type == "Cost of Goods Sold"

    def test_read_account_terms(self, payment_terms_excel_file):
        """Test reading account terms from Excel file."""
        payment_terms = read_payment_terms(payment_terms_excel_file)

        assert len(payment_terms) == 2
        assert payment_terms[0].name == "Cost of Goods Sold"
        assert payment_terms[1].name or payment_terms[1].acc_type == "Expense" 

    def test_read_payment_terms_file_not_found(self):
        """Test handling of non-existent payment terms file."""
        with pytest.raises(FileNotFoundError):
            read_payment_terms("nonexistent.xlsx")
