"""Tests for schema validation and transparent cleaning."""

import pandas as pd
import pytest

from src.expense_tracker.data_cleaning import (
    clean_transactions,
    read_transactions,
    validate_transaction_columns,
)


def test_cleaning_aliases_duplicates_and_invalid_rows():
    rows = [
        ["id-1", "2024-01-01", " food ", "shop", "10", "debit"],
        ["id-1", "2024-01-02", "Food", "second", "11", "expense"],
        ["id-2", "2024-01-03", "Food", "shop", "12", "expense"],
        ["id-3", "not-a-date", "Food", "bad date", "13", "expense"],
        ["id-4", "2024-01-04", "Food", "bad amount", "nope", "expense"],
        ["id-5", "2024-01-05", "Food", "negative", "-5", "expense"],
        ["id-6", "2024-01-06", "Food", "zero", "0", "expense"],
        ["id-7", "2024-01-07", "Food", "unknown type", "4", "transfer"],
        ["id-8", "2024-01-08", "", "missing category", "5", "income"],
        ["id-9", "2024-01-09", "Food", "duplicate", "9", "expense"],
        ["id-9", "2024-01-09", "Food", "duplicate", "9", "expense"],
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            "transaction_id",
            "transaction_date",
            "category",
            "description",
            "value",
            "transaction_type",
        ],
    )

    cleaned, quality = clean_transactions(frame)

    assert len(cleaned) == 3
    assert cleaned["Type"].tolist() == ["Expense", "Expense", "Expense"]
    assert cleaned["Category"].tolist() == ["Food", "Food", "Food"]
    assert quality["input_rows"] == 11
    assert quality["valid_rows"] == 3
    assert quality["removed_rows"] == 8
    assert quality["removal_reasons"] == {
        "duplicate_transaction_id": 1,
        "invalid_date": 1,
        "invalid_amount": 2,
        "negative_amount": 1,
        "invalid_type": 1,
        "missing_critical_fields": 1,
        "exact_duplicate": 1,
    }


def test_cleaning_optional_fields_and_income_debit_semantics():
    frame = pd.DataFrame(
        {"Date": ["2024-01-01"], "Category": ["  salary  "], "Amount": ["25"], "Type": ["credit"]}
    )

    cleaned, quality = clean_transactions(frame)

    assert cleaned.loc[0, "Category"] == "Salary"
    assert cleaned.loc[0, "Type"] == "Income"
    assert cleaned.loc[0, "Payment_Method"] == "Unknown"
    assert quality["removed_rows"] == 0


def test_schema_validation_reports_missing_required_fields():
    with pytest.raises(ValueError, match="Missing required CSV column"):
        validate_transaction_columns(pd.DataFrame({"date": ["2024-01-01"], "value": [1]}))


def test_schema_validation_rejects_ambiguous_aliases():
    with pytest.raises(ValueError, match="map to the same field"):
        validate_transaction_columns(
            pd.DataFrame(
                {
                    "Date": ["2024-01-01"],
                    "transaction_date": ["2024-01-01"],
                    "Category": ["Food"],
                    "Amount": [1],
                    "Type": ["Expense"],
                }
            )
        )


def test_csv_bytes_reading_and_malformed_input():
    valid = b"transaction_date,category,value,transaction_type\n2024-01-01,Food,2,expense\n"
    result = read_transactions(valid)
    assert list(result.columns) == ["Date", "Category", "Amount", "Type"]
    with pytest.raises(ValueError, match="well-formed UTF-8 CSV"):
        read_transactions(b"\xff\xfe")
