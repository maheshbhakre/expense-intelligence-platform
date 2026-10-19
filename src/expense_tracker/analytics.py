"""Reusable descriptive financial analytics with safe empty-data behavior."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

TRANSACTION_COLUMNS = ("Date", "Category", "Amount", "Type")


def _transactions(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in TRANSACTION_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("Analytics require cleaned columns: " + ", ".join(missing))
    data = frame.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Amount"] = pd.to_numeric(data["Amount"], errors="coerce")
    data = data.dropna(subset=["Date", "Amount", "Type", "Category"])
    return data[data["Amount"] > 0]


def summarize_transactions(frame: pd.DataFrame) -> dict[str, float | int]:
    """Calculate key metrics; amount magnitudes are always positive."""
    data = _transactions(frame)
    expenses = data.loc[data["Type"].eq("Expense"), "Amount"]
    income = data.loc[data["Type"].eq("Income"), "Amount"]
    total_income = float(income.sum())
    total_expenses = float(expenses.sum())
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
        "savings_rate": (
            (total_income - total_expenses) / total_income * 100
            if total_income > 0
            else 0.0
        ),
        "average_transaction_value": float(data["Amount"].mean()) if not data.empty else 0.0,
        "transaction_count": int(len(data)),
    }


def category_spending(frame: pd.DataFrame) -> pd.DataFrame:
    """Return expense totals and contribution percentages by category."""
    data = _transactions(frame)
    expenses = data[data["Type"].eq("Expense")]
    result = (
        expenses.groupby("Category", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    total = float(result["Amount"].sum())
    result["Percentage"] = result["Amount"] / total * 100 if total else 0.0
    return result


def monthly_cash_flow(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate income, expenses, balance and savings rate by calendar month.

    Months between the first and last transaction are retained with zero
    activity to avoid hiding gaps in the observed period.
    """
    data = _transactions(frame)
    columns = ["Month", "Income", "Expenses", "Net_Cash_Flow", "Savings_Rate"]
    if data.empty:
        return pd.DataFrame(columns=columns)
    data["Month"] = data["Date"].dt.to_period("M")
    totals = (
        data.pivot_table(
            index="Month",
            columns="Type",
            values="Amount",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(pd.period_range(data["Month"].min(), data["Month"].max(), freq="M"), fill_value=0)
    )
    income = totals["Income"] if "Income" in totals else pd.Series(0.0, index=totals.index)
    expenses = (
        totals["Expense"] if "Expense" in totals else pd.Series(0.0, index=totals.index)
    )
    result = pd.DataFrame(
        {
            "Month": totals.index.astype(str),
            "Income": income.to_numpy(dtype=float),
            "Expenses": expenses.to_numpy(dtype=float),
        }
    )
    result["Net_Cash_Flow"] = result["Income"] - result["Expenses"]
    result["Savings_Rate"] = np.where(
        result["Income"] > 0,
        result["Net_Cash_Flow"] / result["Income"] * 100,
        0.0,
    )
    return result


def weekday_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize expense count and value by weekday in calendar order."""
    data = _transactions(frame)
    expenses = data[data["Type"].eq("Expense")]
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if expenses.empty:
        return pd.DataFrame(columns=["Weekday", "Transactions", "Amount"])
    result = (
        expenses.assign(Weekday=expenses["Date"].dt.day_name())
        .groupby("Weekday")
        .agg(Transactions=("Amount", "size"), Amount=("Amount", "sum"))
        .reindex(order, fill_value=0)
        .rename_axis("Weekday")
        .reset_index()
    )
    return result


def weekday_category_heatmap(frame: pd.DataFrame) -> pd.DataFrame:
    """Return expense totals by category and weekday for heatmap charts."""
    data = _transactions(frame)
    expenses = data[data["Type"].eq("Expense")].copy()
    if expenses.empty:
        return pd.DataFrame(columns=["Category", "Weekday", "Amount"])
    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    return (
        expenses.assign(Weekday=expenses["Date"].dt.day_name())
        .groupby(["Category", "Weekday"], as_index=False)["Amount"]
        .sum()
        .assign(_weekday_order=lambda result: result["Weekday"].map(
            {weekday: index for index, weekday in enumerate(weekday_order)}
        ))
        .sort_values(["Category", "_weekday_order"], kind="stable")
        .drop(columns="_weekday_order")
        .reset_index(drop=True)
    )


def payment_method_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """Return transaction count and amount by payment method and type."""
    data = _transactions(frame)
    if "Payment_Method" not in data:
        data["Payment_Method"] = "Unknown"
    return (
        data.groupby(["Payment_Method", "Type"], as_index=False)
        .agg(Transactions=("Amount", "size"), Amount=("Amount", "sum"))
        .sort_values("Amount", ascending=False, kind="stable")
        .reset_index(drop=True)
    )


def recurring_expenses(
    frame: pd.DataFrame, minimum_months: int = 3, tolerance: float = 0.05
) -> pd.DataFrame:
    """Identify same-description costs observed in distinct months.

    Rule: at least ``minimum_months`` distinct calendar months, with each
    amount within the configured relative tolerance (minimum ₹10) of that
    category/description group's median. This is a descriptive heuristic, not
    a claim that a merchant billed an exact contractual recurring schedule.
    """
    data = _transactions(frame)
    columns = ["Category", "Description", "Occurrences", "Active_Months", "Median_Amount"]
    expenses = data[data["Type"].eq("Expense")].copy()
    if expenses.empty:
        return pd.DataFrame(columns=columns)
    if "Description" not in expenses:
        expenses["Description"] = ""
    expenses["Description"] = expenses["Description"].fillna("").astype(str).str.strip()
    expenses["Month"] = expenses["Date"].dt.to_period("M")
    records: list[dict[str, object]] = []
    for (category, description), group in expenses.groupby(
        ["Category", "Description"], dropna=False
    ):
        median = float(group["Amount"].median())
        close = (group["Amount"] - median).abs() <= max(10.0, median * tolerance)
        selected = group.loc[close]
        active_months = int(selected["Month"].nunique())
        if active_months >= minimum_months:
            records.append(
                {
                    "Category": category,
                    "Description": description or "(description not provided)",
                    "Occurrences": int(len(selected)),
                    "Active_Months": active_months,
                    "Median_Amount": median,
                }
            )
    return pd.DataFrame.from_records(records, columns=columns).sort_values(
        ["Active_Months", "Occurrences"], ascending=False, kind="stable"
    ).reset_index(drop=True)


def budget_utilization(
    frame: pd.DataFrame,
    budgets: Mapping[str, float],
    months_in_scope: int = 1,
) -> pd.DataFrame:
    """Compare filtered category expenses with monthly budgets over a period."""
    if months_in_scope < 1:
        raise ValueError("months_in_scope must be at least 1.")
    data = _transactions(frame)
    expenses = data[data["Type"].eq("Expense")].groupby("Category")["Amount"].sum()
    categories = sorted(set(expenses.index).union(budgets.keys()))
    rows: list[dict[str, object]] = []
    for category in categories:
        monthly_budget = float(budgets.get(category, 0.0))
        period_budget = monthly_budget * months_in_scope
        spent = float(expenses.get(category, 0.0))
        rows.append(
            {
                "Category": category,
                "Spent": spent,
                "Monthly_Budget": monthly_budget,
                "Period_Budget": period_budget,
                "Utilization_Percent": spent / period_budget * 100 if period_budget else np.nan,
                "Over_Budget": bool(period_budget > 0 and spent > period_budget),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "Category",
            "Spent",
            "Monthly_Budget",
            "Period_Budget",
            "Utilization_Percent",
            "Over_Budget",
        ],
    )


def month_over_month_spending(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare expense totals with the immediately preceding calendar month."""
    monthly = monthly_cash_flow(frame)
    columns = ["Month", "Expenses", "Previous_Expenses", "Change", "Change_Percent"]
    if monthly.empty:
        return pd.DataFrame(columns=columns)
    result = monthly[["Month", "Expenses"]].copy()
    result["Previous_Expenses"] = result["Expenses"].shift(1)
    result["Change"] = result["Expenses"] - result["Previous_Expenses"]
    result["Change_Percent"] = np.where(
        result["Previous_Expenses"] > 0,
        result["Change"] / result["Previous_Expenses"] * 100,
        np.nan,
    )
    return result[columns]


def detect_unusual_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    """Flag high expense outliers by category using the 1.5×IQR upper fence."""
    data = _transactions(frame)
    expenses = data[data["Type"].eq("Expense")].copy()
    if expenses.empty:
        expenses["IQR_Upper_Bound"] = pd.Series(dtype=float)
        return expenses
    bounds: dict[object, float] = {}
    for category, group in expenses.groupby("Category"):
        if len(group) < 4:
            continue
        q1 = float(group["Amount"].quantile(0.25))
        q3 = float(group["Amount"].quantile(0.75))
        bounds[category] = q3 + 1.5 * (q3 - q1)
    expenses["IQR_Upper_Bound"] = expenses["Category"].map(bounds)
    return (
        expenses[expenses["IQR_Upper_Bound"].notna()]
        .loc[lambda rows: rows["Amount"] > rows["IQR_Upper_Bound"]]
        .sort_values("Amount", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
