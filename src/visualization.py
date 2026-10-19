"""Backward-compatible static chart generator."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from expense_tracker.analytics import category_spending, monthly_cash_flow
    from expense_tracker.data_cleaning import clean_transactions, read_transactions
except ModuleNotFoundError as exc:
    if exc.name != "expense_tracker":
        raise
    from src.expense_tracker.analytics import category_spending, monthly_cash_flow
    from src.expense_tracker.data_cleaning import clean_transactions, read_transactions

ROOT = Path(__file__).resolve().parents[1]


def generate_charts(
    source: str | Path | None = None,
    output_dir: str | Path = "outputs/charts",
) -> list[Path]:
    """Generate static charts from cleaned data, handling empty expense sets."""
    if source is None:
        candidates = (
            ROOT / "data" / "processed" / "transactions_cleaned.csv",
            ROOT / "data" / "cleaned_expenses.csv",
        )
        source_path = next((path for path in candidates if path.exists()), None)
        if source_path is None:
            raise FileNotFoundError("Run `python main.py` before generating charts.")
    else:
        source_path = Path(source)
    cleaned, _ = clean_transactions(read_transactions(source_path))
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    generated: list[Path] = []

    categories = category_spending(cleaned)
    figure, axis = plt.subplots(figsize=(10, 5))
    if categories.empty:
        axis.text(0.5, 0.5, "No expense transactions", ha="center", va="center")
        axis.set_axis_off()
    else:
        sns.barplot(data=categories, x="Category", y="Amount", hue="Category", legend=False, ax=axis)
        axis.set_title("Category-wise Spending")
        axis.set_ylabel("Amount (INR)")
        axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    target = destination / "category_spending.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    generated.append(target)

    figure, axis = plt.subplots(figsize=(7, 7))
    if categories.empty:
        axis.text(0.5, 0.5, "No expense transactions", ha="center", va="center")
        axis.set_axis_off()
    else:
        axis.pie(categories["Amount"], labels=categories["Category"], autopct="%1.1f%%")
        axis.set_title("Expense Distribution")
    figure.tight_layout()
    target = destination / "pie_chart.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    generated.append(target)

    monthly = monthly_cash_flow(cleaned)
    figure, axis = plt.subplots(figsize=(10, 5))
    if monthly.empty:
        axis.text(0.5, 0.5, "No monthly data", ha="center", va="center")
        axis.set_axis_off()
    else:
        axis.plot(monthly["Month"], monthly["Expenses"], marker="o")
        axis.set_title("Monthly Expense Trend")
        axis.set_xlabel("Month")
        axis.set_ylabel("Expenses (INR)")
        axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    target = destination / "monthly_trend.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    generated.append(target)
    return generated


if __name__ == "__main__":
    for chart in generate_charts():
        print(f"Saved {chart}")
