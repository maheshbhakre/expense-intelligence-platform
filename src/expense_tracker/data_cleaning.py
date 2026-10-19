"""CSV validation, canonicalization, and auditable transaction cleaning."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import IO

import pandas as pd

REQUIRED_COLUMNS = ("Date", "Category", "Amount", "Type")
COLUMN_ALIASES = {
    "transactionid": "Transaction_ID",
    "transactionidentifier": "Transaction_ID",
    "id": "Transaction_ID",
    "date": "Date",
    "transactiondate": "Date",
    "category": "Category",
    "description": "Description",
    "details": "Description",
    "amount": "Amount",
    "value": "Amount",
    "type": "Type",
    "transactiontype": "Type",
    "paymentmethod": "Payment_Method",
    "paymentmode": "Payment_Method",
    "month": "Month",
    "monthnum": "Month_Num",
    "weekday": "Weekday",
}
TYPE_ALIASES = {
    "expense": "Expense",
    "expenses": "Expense",
    "debit": "Expense",
    "outflow": "Expense",
    "income": "Income",
    "credit": "Income",
    "inflow": "Income",
}


def normalize_column_name(column: object) -> str:
    """Map a human-readable or common alias header to a canonical name."""
    normalized = "".join(char.lower() for char in str(column) if char.isalnum())
    return COLUMN_ALIASES.get(normalized, str(column).strip())


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with standardized headers and reject ambiguous collisions."""
    result = frame.copy()
    names = [normalize_column_name(column) for column in result.columns]
    duplicates = pd.Index(names)[pd.Index(names).duplicated()].unique().tolist()
    if duplicates:
        raise ValueError(
            "CSV contains multiple columns that map to the same field: "
            + ", ".join(duplicates)
            + ". Keep only one version of each field."
        )
    result.columns = names
    return result


def validate_transaction_columns(frame: pd.DataFrame) -> None:
    """Raise an actionable error when required transaction columns are absent."""
    normalized = normalize_columns(frame).reset_index(drop=True)
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized]
    if missing:
        raise ValueError(
            "Missing required CSV column(s): "
            + ", ".join(missing)
            + ". Required fields are Date, Category, Amount, and Type. "
            "Common aliases such as transaction_date, value, and transaction_type are supported."
        )


def read_transactions(source: str | Path | bytes | IO[bytes]) -> pd.DataFrame:
    """Read a CSV path or byte stream, validating its required schema."""
    try:
        csv_source = BytesIO(source) if isinstance(source, bytes) else source
        frame = pd.read_csv(csv_source)
    except (pd.errors.ParserError, UnicodeDecodeError, OSError, ValueError) as exc:
        raise ValueError(
            "Could not read this CSV. Check that it is a well-formed UTF-8 CSV "
            "with a header row and comma-separated fields."
        ) from exc
    if frame.empty and len(frame.columns) == 0:
        raise ValueError("The CSV is empty or has no header row.")
    validate_transaction_columns(frame)
    return normalize_columns(frame)


def _empty_quality_summary() -> dict[str, object]:
    return {
        "input_rows": 0,
        "valid_rows": 0,
        "removed_rows": 0,
        "removal_reasons": {},
        "missing_values": {},
    }


def clean_transactions(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Normalize valid transactions and report every removed row by reason.

    Duplicate rule: exact duplicate rows are removed first; if a nonblank
    Transaction_ID exists, subsequent records sharing an ID are duplicates.
    Amounts are positive magnitudes and Type controls cash-flow direction, so
    zero and negative amounts are excluded instead of silently reinterpreted.
    """
    normalized = normalize_columns(frame).reset_index(drop=True)
    validate_transaction_columns(normalized)
    input_rows = len(normalized)
    if input_rows == 0:
        return normalized.assign(Date=pd.Series(dtype="datetime64[ns]")), _empty_quality_summary()

    original_missing = {
        str(column): int(normalized[column].isna().sum())
        for column in normalized.columns
        if int(normalized[column].isna().sum()) > 0
    }
    work = normalized.copy()
    work["_removal_reason"] = pd.Series(index=work.index, dtype="object")

    exact_duplicates = work.drop(columns="_removal_reason").duplicated(keep="first")
    work.loc[exact_duplicates, "_removal_reason"] = "exact_duplicate"
    if "Transaction_ID" in work.columns:
        identifiers = work["Transaction_ID"].astype("string").str.strip()
        has_identifier = identifiers.notna() & identifiers.ne("")
        duplicate_ids = has_identifier & identifiers.duplicated(keep="first")
        work.loc[duplicate_ids & work["_removal_reason"].isna(), "_removal_reason"] = (
            "duplicate_transaction_id"
        )

    remaining = work["_removal_reason"].isna()
    category = work.get("Category", pd.Series(index=work.index, dtype="object"))
    raw_type = work.get("Type", pd.Series(index=work.index, dtype="object"))
    missing_critical = (
        work["Date"].isna()
        | category.isna()
        | category.astype("string").str.strip().eq("").fillna(True)
        | work["Amount"].isna()
        | raw_type.isna()
        | raw_type.astype("string").str.strip().eq("").fillna(True)
    )
    work.loc[remaining & missing_critical, "_removal_reason"] = "missing_critical_fields"

    remaining = work["_removal_reason"].isna()
    parsed_dates = pd.to_datetime(work["Date"], errors="coerce")
    work.loc[remaining & parsed_dates.isna(), "_removal_reason"] = "invalid_date"

    amount = pd.to_numeric(work["Amount"], errors="coerce")
    remaining = work["_removal_reason"].isna()
    negative_amount = amount.lt(0)
    work.loc[remaining & negative_amount, "_removal_reason"] = "negative_amount"
    remaining = work["_removal_reason"].isna()
    invalid_amount = amount.isna() | amount.eq(0)
    work.loc[remaining & invalid_amount, "_removal_reason"] = "invalid_amount"

    normalized_types = (
        raw_type.astype("string").str.strip().str.casefold().map(TYPE_ALIASES)
    )
    remaining = work["_removal_reason"].isna()
    work.loc[remaining & normalized_types.isna(), "_removal_reason"] = "invalid_type"

    reasons = {
        str(reason): int(count)
        for reason, count in work["_removal_reason"].value_counts().items()
    }
    cleaned = work.loc[work["_removal_reason"].isna()].drop(columns="_removal_reason").copy()
    cleaned["Date"] = parsed_dates.loc[cleaned.index]
    cleaned["Amount"] = amount.loc[cleaned.index].astype(float)
    cleaned["Type"] = normalized_types.loc[cleaned.index]
    cleaned["Category"] = cleaned["Category"].astype("string").str.strip().str.title()
    if "Description" not in cleaned:
        cleaned["Description"] = ""
    else:
        cleaned["Description"] = (
            cleaned["Description"].fillna("").astype("string").str.strip()
        )
    if "Payment_Method" not in cleaned:
        cleaned["Payment_Method"] = "Unknown"
    else:
        cleaned["Payment_Method"] = (
            cleaned["Payment_Method"]
            .fillna("Unknown")
            .astype("string")
            .str.strip()
            .replace("", "Unknown")
            .str.title()
        )
    if "Transaction_ID" in cleaned:
        cleaned["Transaction_ID"] = cleaned["Transaction_ID"].astype("string").str.strip()
    cleaned["Month"] = cleaned["Date"].dt.month_name()
    cleaned["Month_Num"] = cleaned["Date"].dt.month
    cleaned["Weekday"] = cleaned["Date"].dt.day_name()
    cleaned = cleaned.reset_index(drop=True)

    return cleaned, {
        "input_rows": input_rows,
        "valid_rows": len(cleaned),
        "removed_rows": input_rows - len(cleaned),
        "removal_reasons": reasons,
        "missing_values": original_missing,
    }
