"""Tests for descriptive metrics, budgets, recurring costs, and anomalies."""

import pandas as pd

from src.expense_tracker.analytics import (
    budget_utilization,
    category_spending,
    detect_unusual_transactions,
    month_over_month_spending,
    monthly_cash_flow,
    recurring_expenses,
    summarize_transactions,
    weekday_category_heatmap,
)
from src.expense_tracker.forecasting import forecast_next_month_expenses


def test_income_expense_balance_savings_and_average(transactions):
    metrics = summarize_transactions(transactions)

    assert metrics["total_income"] == 10_000
    assert metrics["total_expenses"] == 2_100
    assert metrics["net_balance"] == 7_900
    assert metrics["savings_rate"] == 79
    assert metrics["average_transaction_value"] == 4_033.3333333333335
    assert metrics["transaction_count"] == 3


def test_zero_income_savings_rate_and_empty_metrics():
    expenses = pd.DataFrame(
        [{"Date": "2024-01-01", "Category": "Food", "Amount": 100, "Type": "Expense"}]
    )
    assert summarize_transactions(expenses)["savings_rate"] == 0
    assert summarize_transactions(expenses)["net_balance"] == -100
    empty = pd.DataFrame(columns=["Date", "Category", "Amount", "Type"])
    assert summarize_transactions(empty)["transaction_count"] == 0
    assert monthly_cash_flow(empty).empty
    assert category_spending(empty).empty


def test_category_contribution_and_monthly_gaps(transactions):
    categories = category_spending(transactions)
    assert categories.loc[0, "Category"] == "Food"
    assert categories.loc[0, "Percentage"] == 100

    with_gap = pd.concat(
        [
            transactions,
            pd.DataFrame(
                [{"Date": "2024-03-05", "Category": "Food", "Amount": 100, "Type": "Expense"}]
            ),
        ],
        ignore_index=True,
    )
    monthly = monthly_cash_flow(with_gap)
    assert monthly["Month"].tolist() == ["2024-01", "2024-02", "2024-03"]
    assert monthly.loc[1, "Income"] == 0
    assert monthly.loc[1, "Net_Cash_Flow"] == -1_100
    heatmap = weekday_category_heatmap(transactions)
    assert set(heatmap["Category"]) == {"Food"}
    assert heatmap["Amount"].sum() == 2_100


def test_budget_calculation_and_over_budget(transactions):
    result = budget_utilization(transactions, {"Food": 1_000, "Rent": 2_000}, months_in_scope=2)
    food = result.set_index("Category").loc["Food"]
    rent = result.set_index("Category").loc["Rent"]
    assert food["Period_Budget"] == 2_000
    assert food["Utilization_Percent"] == 105
    assert bool(food["Over_Budget"])
    assert not bool(rent["Over_Budget"])


def test_recurring_rule_and_category_iqr_outlier():
    rows = [
        {"Date": f"2024-0{month}-05", "Category": "Internet", "Description": "Monthly bill", "Amount": amount, "Type": "Expense"}
        for month, amount in [(1, 1_000), (2, 1_020), (3, 990)]
    ]
    rows.extend(
        [
            {"Date": f"2024-01-{day:02d}", "Category": "Dining", "Description": "Meal", "Amount": value, "Type": "Expense"}
            for day, value in enumerate([10, 11, 12, 13, 100], start=1)
        ]
    )
    frame = pd.DataFrame(rows)

    recurring = recurring_expenses(frame)
    unusual = detect_unusual_transactions(frame)

    assert recurring.loc[0, "Description"] == "Monthly bill"
    assert recurring.loc[0, "Active_Months"] == 3
    assert unusual.iloc[0]["Amount"] == 100
    assert unusual.iloc[0]["IQR_Upper_Bound"] == 16


def test_monthly_change_and_forecast_are_labeled(transactions):
    changes = month_over_month_spending(transactions)
    assert changes.loc[1, "Change"] == 100
    forecast = forecast_next_month_expenses(transactions)
    assert forecast.empty

    three_months = pd.concat(
        [
            transactions,
            pd.DataFrame(
                [{"Date": "2024-03-01", "Category": "Food", "Amount": 300, "Type": "Expense"}]
            ),
        ],
        ignore_index=True,
    )
    forecast = forecast_next_month_expenses(three_months)
    assert forecast.loc[0, "Month"] == "2024-04"
    assert forecast.loc[0, "Forecast_Expenses"] == 800
    assert "arithmetic mean" in forecast.loc[0, "Method"]
