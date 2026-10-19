"""Tests for simulated transaction generation."""

import pandas as pd

from src.expense_tracker.data_generator import generate_transactions, write_synthetic_data


def test_generation_is_deterministic_and_covers_two_years():
    first = generate_transactions(seed=17)
    second = generate_transactions(seed=17)

    pd.testing.assert_frame_equal(first, second)
    assert len(first) >= 1_500
    assert first["Date"].dt.to_period("M").nunique() == 24
    assert first["Date"].min() < first["Date"].max()
    assert first["Transaction_ID"].is_unique
    assert first["Transaction_ID"].str.startswith("SIM-").all()
    assert set(first["Type"]) == {"Income", "Expense"}
    assert (first["Amount"] > 0).all()
    assert first.loc[first["Type"].eq("Income"), "Category"].nunique() > 1


def test_generation_rejects_invalid_month_count():
    try:
        generate_transactions(months=11)
    except ValueError as error:
        assert "between 12 and 24" in str(error)
    else:
        raise AssertionError("Invalid month count should be rejected.")


def test_write_synthetic_data_creates_parent_and_csv(tmp_path):
    path = tmp_path / "raw" / "sample.csv"
    frame = write_synthetic_data(path, months=12, seed=4)

    saved = pd.read_csv(path)
    assert len(frame) == len(saved)
    assert saved["Transaction_ID"].is_unique
