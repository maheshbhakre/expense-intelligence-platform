"""Deterministic generation of realistic, clearly simulated transactions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_SEED = 42
DEFAULT_MONTHS = 24
DEFAULT_TRANSACTIONS_PER_MONTH = 80
EXPENSE_CATEGORIES = (
    "Groceries",
    "Housing",
    "Utilities",
    "Transport",
    "Healthcare",
    "Dining",
    "Entertainment",
    "Shopping",
    "Subscriptions",
    "Education",
    "Travel",
    "Personal Care",
)
INCOME_CATEGORIES = ("Salary", "Freelance", "Investment Income")
PAYMENT_METHODS = ("UPI", "Card", "Cash", "Bank Transfer", "Auto-debit")
EXPENSE_DESCRIPTIONS = {
    "Groceries": ("Weekly groceries", "Fresh produce", "Household supplies"),
    "Housing": ("Home maintenance",),
    "Utilities": ("Electricity bill", "Internet bill", "Water bill"),
    "Transport": ("Metro pass", "Fuel", "Ride share"),
    "Healthcare": ("Pharmacy", "Clinic visit", "Health check-up"),
    "Dining": ("Restaurant", "Cafe", "Food delivery"),
    "Entertainment": ("Movie tickets", "Event ticket", "Digital entertainment"),
    "Shopping": ("Clothing", "Home goods", "Online purchase"),
    "Subscriptions": ("Music subscription", "Cloud subscription", "Software plan"),
    "Education": ("Course fee", "Books and supplies", "Learning material"),
    "Travel": ("Train ticket", "Hotel booking", "Travel booking"),
    "Personal Care": ("Personal care", "Salon visit", "Wellness"),
}
RECURRING_MONTHLY_COSTS = (
    ("Housing", "Monthly rent", 18_000, "Auto-debit"),
    ("Subscriptions", "Music subscription", 199, "Auto-debit"),
    ("Utilities", "Internet bill", 999, "Auto-debit"),
)


def generate_transactions(
    seed: int = DEFAULT_SEED,
    months: int = DEFAULT_MONTHS,
    transactions_per_month: int = DEFAULT_TRANSACTIONS_PER_MONTH,
    start_date: str | pd.Timestamp = "2024-01-01",
) -> pd.DataFrame:
    """Return reproducible positive-amount income and expense transactions.

    Income/expense semantics are represented by ``Type``; ``Amount`` is always
    a positive magnitude. Recurring examples use the same category,
    description, and amount every month so rule-based detection is testable.
    """
    if not 12 <= months <= 24:
        raise ValueError("months must be between 12 and 24.")
    if transactions_per_month < 10:
        raise ValueError("transactions_per_month must be at least 10.")

    start = pd.Timestamp(start_date).normalize().replace(day=1)
    rng = np.random.default_rng(seed)
    records: list[dict[str, object]] = []
    serial = 1
    expense_weights = np.array(
        [0.19, 0.12, 0.10, 0.12, 0.05, 0.12, 0.07, 0.08, 0.04, 0.03, 0.03, 0.05]
    )
    payment_weights = np.array([0.38, 0.25, 0.13, 0.12, 0.12])

    for month_offset in range(months):
        month_start = start + pd.DateOffset(months=month_offset)
        month_end = month_start + pd.offsets.MonthEnd(0)
        days_in_month = int(month_end.day)
        month_records: list[dict[str, object]] = []

        for category, description, amount, payment in RECURRING_MONTHLY_COSTS:
            month_records.append(
                {
                    "Transaction_ID": f"SIM-{serial:06d}",
                    "Date": month_start + pd.Timedelta(days=4),
                    "Category": category,
                    "Description": description,
                    "Amount": amount,
                    "Type": "Expense",
                    "Payment_Method": payment,
                }
            )
            serial += 1

        income_sources = [
            ("Salary", int(rng.integers(35_000, 65_001)), "Monthly simulated salary")
        ]
        if rng.random() < 0.35:
            income_sources.append(
                ("Freelance", int(rng.integers(4_000, 15_001)), "Simulated freelance work")
            )
        if rng.random() < 0.12:
            income_sources.append(
                (
                    "Investment Income",
                    int(rng.integers(500, 5_001)),
                    "Simulated investment distribution",
                )
            )
        for income_source, income_amount, description in income_sources:
            month_records.append(
                {
                    "Transaction_ID": f"SIM-{serial:06d}",
                    "Date": month_start,
                    "Category": income_source,
                    "Description": description,
                    "Amount": income_amount,
                    "Type": "Income",
                    "Payment_Method": "Bank Transfer",
                }
            )
            serial += 1

        for _ in range(transactions_per_month - len(month_records)):
            category = str(rng.choice(EXPENSE_CATEGORIES, p=expense_weights))
            description = str(rng.choice(EXPENSE_DESCRIPTIONS[category]))
            low, high = {
                "Groceries": (100, 601),
                "Housing": (300, 1_501),
                "Utilities": (100, 1_201),
                "Transport": (30, 401),
                "Healthcare": (100, 1_501),
                "Dining": (80, 601),
                "Entertainment": (100, 1_001),
                "Shopping": (100, 1_201),
                "Subscriptions": (99, 401),
                "Education": (200, 2_001),
                "Travel": (300, 3_001),
                "Personal Care": (75, 501),
            }[category]
            month_records.append(
                {
                    "Transaction_ID": f"SIM-{serial:06d}",
                    "Date": month_start
                    + pd.Timedelta(days=int(rng.integers(0, days_in_month))),
                    "Category": category,
                    "Description": description,
                    "Amount": int(rng.integers(low, high)),
                    "Type": "Expense",
                    "Payment_Method": rng.choice(PAYMENT_METHODS, p=payment_weights),
                }
            )
            serial += 1

        records.extend(month_records)

    frame = pd.DataFrame.from_records(records)
    return frame.sort_values(["Date", "Transaction_ID"], kind="stable").reset_index(drop=True)


def write_synthetic_data(
    output_path: str | Path = "data/raw/transactions.csv",
    **generator_options: int | str | pd.Timestamp,
) -> pd.DataFrame:
    """Generate and save simulated transactions without modifying other inputs."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_transactions(**generator_options)
    frame.to_csv(destination, index=False)
    return frame


if __name__ == "__main__":
    generated = write_synthetic_data()
    print(
        f"Generated {len(generated):,} simulated transactions "
        f"({generated['Date'].min():%Y-%m} to {generated['Date'].max():%Y-%m})."
    )
