"""Simple transparent forecast baselines, explicitly separate from analytics."""

from __future__ import annotations

import pandas as pd

from .analytics import monthly_cash_flow


def forecast_next_month_expenses(frame: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Forecast one month with a trailing mean of observed monthly expenses.

    This descriptive baseline is shown only when at least ``window`` calendar
    months are available. It is not a fitted model and provides no confidence
    interval.
    """
    if window < 1:
        raise ValueError("window must be at least 1.")
    monthly = monthly_cash_flow(frame)
    if len(monthly) < window:
        return pd.DataFrame(columns=["Month", "Forecast_Expenses", "Method"])
    last_month = pd.Period(monthly["Month"].iloc[-1], freq="M")
    estimate = float(monthly["Expenses"].tail(window).mean())
    return pd.DataFrame(
        [
            {
                "Month": str(last_month + 1),
                "Forecast_Expenses": estimate,
                "Method": f"Trailing {window}-month arithmetic mean",
            }
        ]
    )
