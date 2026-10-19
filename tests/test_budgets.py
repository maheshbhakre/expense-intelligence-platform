"""Tests for locally stored budget configuration."""

import json

import pytest

from src.expense_tracker.budgets import DEFAULT_MONTHLY_BUDGETS, load_budgets, save_budgets


def test_budget_defaults_save_and_reload(tmp_path):
    path = tmp_path / "data" / "budgets.json"
    assert load_budgets(path) == DEFAULT_MONTHLY_BUDGETS
    save_budgets({" food ": 1_250}, path)
    assert load_budgets(path) == {"Food": 1_250.0}


def test_invalid_budget_file_is_not_silently_ignored(tmp_path):
    path = tmp_path / "budgets.json"
    path.write_text(json.dumps({"Food": -1}), encoding="utf-8")
    with pytest.raises(ValueError, match="positive number"):
        load_budgets(path)
