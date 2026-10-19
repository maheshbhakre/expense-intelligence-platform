"""Run the backward-compatible static chart generation workflow."""

from src.visualization import generate_charts


if __name__ == "__main__":
    for chart in generate_charts():
        print(f"Saved {chart}")
