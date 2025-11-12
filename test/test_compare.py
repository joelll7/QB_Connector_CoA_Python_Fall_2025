from src.compare import compare_account_types
from src.models import Account


def test_compare_account_types() -> None:
    excel_terms = [
        Account(
            AccountType="ASSET", number="10000", name="Asset", id="1", source="excel"
        ),
        Account(
            AccountType="INCOME", number="11000", name="Income", id="2", source="excel"
        ),
        Account(
            AccountType="EXPENSE",
            number="12000",
            name="Expense",
            id="3",
            source="excel",
        ),
    ]

    qb_terms = [
        Account(
            AccountType="EXPENSE",
            number="10000",
            name="Expenses",
            id="1",
            source="quickbooks",
        ),
        Account(
            AccountType="INCOME",
            number="11000",
            name="Income",
            id="2",
            source="quickbooks",
        ),
        Account(
            AccountType="LIABILITY",
            number="12000",
            name="Liability",
            id="3",
            source="quickbooks",
        ),
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
