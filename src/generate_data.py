"""Backward-compatible generator command: ``python src/generate_data.py``."""

from expense_tracker.data_generator import write_synthetic_data


if __name__ == "__main__":
    generated = write_synthetic_data()
    print(
        f"Generated {len(generated):,} simulated transactions in "
        "data/raw/transactions.csv."
    )
