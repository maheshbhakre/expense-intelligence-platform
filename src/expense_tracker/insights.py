"""Explainable summaries built from descriptive analytics."""

from __future__ import annotations

import pandas as pd

from .analytics import (
    category_spending,
    detect_unusual_transactions,
    month_over_month_spending,
    recurring_expenses,
)


def build_spending_insights(frame: pd.DataFrame) -> dict[str, object]:
    """Return data-backed category, trend, recurring and anomaly summaries."""
    categories = category_spending(frame)
    changes = month_over_month_spending(frame)
    recurring = recurring_expenses(frame)
    unusual = detect_unusual_transactions(frame)
    latest_change = changes.iloc[-1] if not changes.empty else None
    return {
        "highest_spending_category": (
            categories.iloc[0].to_dict() if not categories.empty else None
        ),
        "latest_month_change": latest_change.to_dict() if latest_change is not None else None,
        "recurring_expenses": recurring,
        "unusual_transactions": unusual,
    }
