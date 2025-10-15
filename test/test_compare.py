import pytest
from src.compare import compare_account_types
from src.models import AccountTypeModel, ComparisonReport, Conflict, PaymentTerm

def test_compare_account_types():
    excel_terms = [
        PaymentTerm(account_type="ASSET", name="Asset", source="excel"),
        PaymentTerm(account_type="INCOME", name="Income", source="excel"),
        PaymentTerm(account_type="EXPENSE",name="Expense", source="excel")
    ]

    qb_terms = [
        PaymentTerm(account_type="EXPENSE", name="Expenses", source="quickbooks"),
        PaymentTerm(account_type="INCOME", names="Income", source="quickbooks"),
        PaymentTerm(account_type="LIABILITY", name="Liability", source="quickbooks")
    ]
    
    result = compare_account_types(excel_terms, qb_terms)

    assert len(result.excel_only) == 1
    assert result.excel_only[0].account_type == "ASSET"
    
    assert len(result.qb_only) == 1
    assert result.qb_only[0].account_type == "LIABILITY"

    assert len(result.conflicts) == 1
    assert result.conflicts[0].account_type == "EXPENSE"
    assert result.conflicts[0].excel_name == "Expense"
    assert result.conflicts[0].qb_name == "Expenses"
    assert result.conflicts[0].reason == "name_mismatch"

