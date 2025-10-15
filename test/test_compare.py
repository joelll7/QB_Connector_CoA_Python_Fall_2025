import pytest
from src.compare import compare_account_types
from src.models import AccountTypeModel, ComparisonReport, Conflict, PaymentTerm

def test_compare_account_types():
    excel_terms = [
        PaymentTerm(AccountType="ASSET", name="Asset", source="excel"),
        PaymentTerm(AccountType="INCOME", name="Income", source="excel"),
        PaymentTerm(AccountType="EXPENSE",name="Expense", source="excel")
    ]

    qb_terms = [
        PaymentTerm(AccountType="EXPENSE", name="Expenses", source="quickbooks"),
        PaymentTerm(AccountType="INCOME", name="Income", source="quickbooks"),
        PaymentTerm(AccountType="LIABILITY", name="Liability", source="quickbooks")
    ]
    
    result = compare_account_types(excel_terms, qb_terms)

    assert len(result.excel_only) == 1
    assert result.excel_only[0].AccountType == "ASSET"
    
    assert len(result.qb_only) == 1
    assert result.qb_only[0].AccountType == "LIABILITY"

    assert len(result.conflicts) == 1
    assert result.conflicts[0].AccountType == "EXPENSE"
    assert result.conflicts[0].excel_name == "Expense"
    assert result.conflicts[0].qb_name == "Expenses"
    assert result.conflicts[0].reason == "name_mismatch"

