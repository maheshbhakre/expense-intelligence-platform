"""Shared test data fixtures."""

import pandas as pd
import pytest


@pytest.fixture
def transactions() -> pd.DataFrame:
    """Return a compact cleaned-format income and expense dataset."""
    return pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Category": "Salary",
                "Description": "Monthly pay",
                "Amount": 10_000,
                "Type": "Income",
                "Payment_Method": "Bank Transfer",
            },
            {
                "Date": "2024-01-02",
                "Category": "Food",
                "Description": "Groceries",
                "Amount": 1_000,
                "Type": "Expense",
                "Payment_Method": "UPI",
            },
            {
                "Date": "2024-02-02",
                "Category": "Food",
                "Description": "Groceries",
                "Amount": 1_100,
                "Type": "Expense",
                "Payment_Method": "UPI",
            },
        ]
    ).assign(Date=lambda data: pd.to_datetime(data["Date"]))
