"""Clean the default transaction CSV and report data quality and summary metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.expense_tracker.analytics import category_spending, monthly_cash_flow, summarize_transactions
from src.expense_tracker.data_cleaning import clean_transactions, read_transactions

ROOT = Path(__file__).resolve().parent
RAW_CANDIDATES = (
    ROOT / "data" / "raw" / "transactions.csv",
    ROOT / "data" / "expenses.csv",
)
PROCESSED_PATH = ROOT / "data" / "processed" / "transactions_cleaned.csv"
LEGACY_PROCESSED_PATH = ROOT / "data" / "cleaned_expenses.csv"


def process_default_dataset() -> tuple[pd.DataFrame, dict[str, object]]:
    """Clean the generated dataset, falling back to the original legacy CSV."""
    source = next((path for path in RAW_CANDIDATES if path.exists()), None)
    if source is None:
        raise FileNotFoundError(
            "No input transactions found. Run `python generate_data.py` first."
        )
    raw = read_transactions(source)
    cleaned, quality = clean_transactions(raw)
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(PROCESSED_PATH, index=False)
    cleaned.to_csv(LEGACY_PROCESSED_PATH, index=False)
    return cleaned, quality


def main() -> None:
    cleaned, quality = process_default_dataset()
    print(f"Loaded {quality['input_rows']:,} rows; retained {quality['valid_rows']:,}.")
    print(f"Removed {quality['removed_rows']:,} rows: {quality['removal_reasons'] or 'none'}")
    print(f"Saved cleaned data to {PROCESSED_PATH}")
    print("\nFinancial summary:")
    for label, value in summarize_transactions(cleaned).items():
        print(f"  {label}: {value:,.2f}" if isinstance(value, float) else f"  {label}: {value:,}")
    print("\nExpense by category:")
    print(category_spending(cleaned).to_string(index=False))
    print("\nMonthly cash flow:")
    print(monthly_cash_flow(cleaned).to_string(index=False))


if __name__ == "__main__":
    main()
