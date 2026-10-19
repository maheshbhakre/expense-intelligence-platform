"""Validated, local JSON storage for monthly category budget settings."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_MONTHLY_BUDGETS = {
    "Dining": 8_000.0,
    "Groceries": 12_000.0,
    "Housing": 20_000.0,
    "Shopping": 5_000.0,
    "Subscriptions": 1_000.0,
    "Transport": 5_000.0,
    "Utilities": 4_000.0,
}


def validate_budgets(budgets: object) -> dict[str, float]:
    """Validate budget JSON values and return normalized category amounts."""
    if not isinstance(budgets, dict):
        raise ValueError("Budget settings must be a JSON object of category: amount pairs.")
    normalized: dict[str, float] = {}
    for category, amount in budgets.items():
        label = str(category).strip().title()
        try:
            value = float(amount)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Budget for {category!r} must be a positive number.") from exc
        if not label or value <= 0:
            raise ValueError(f"Budget for {category!r} must be a positive number.")
        normalized[label] = value
    return normalized


def load_budgets(path: str | Path = "data/budgets.json") -> dict[str, float]:
    """Load custom budgets or return documented defaults when none are saved."""
    location = Path(path)
    if not location.exists():
        return dict(DEFAULT_MONTHLY_BUDGETS)
    try:
        with location.open(encoding="utf-8") as stream:
            return validate_budgets(json.load(stream))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Could not read budget settings from {location}; fix or remove the JSON file."
        ) from exc


def save_budgets(
    budgets: dict[str, float], path: str | Path = "data/budgets.json"
) -> None:
    """Persist validated local budget settings atomically using a temp file."""
    location = Path(path)
    location.parent.mkdir(parents=True, exist_ok=True)
    validated = validate_budgets(budgets)
    temporary = location.with_suffix(location.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")
        temporary.replace(location)
    except OSError as exc:
        raise ValueError(f"Could not save budget settings to {location}: {exc}") from exc
