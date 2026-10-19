"""Tests for dashboard formatting and truthful KPI comparisons."""

from src.expense_tracker.ui import comparison_text, format_inr


def test_indian_currency_grouping():
    assert format_inr(125_000) == "₹1,25,000"
    assert format_inr(1_234.5) == "₹1,234.50"
    assert format_inr(-12_345) == "-₹12,345"


def test_comparison_displays_n_a_for_zero_baseline():
    assert comparison_text(50, 0) == "N/A vs prior period"
    assert comparison_text(150, 100) == "+50.0% vs prior period"
    assert comparison_text(12, 8, percentage_points=True) == "+4.0 pp vs prior period"
