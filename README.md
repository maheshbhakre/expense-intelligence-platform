# Expense Tracker — Financial Analytics Dashboard

An end-to-end, portfolio-ready data application for exploring income, expenses,
cash flow, spending behavior, category budgets, and data quality. The example
dataset is synthetic and deterministic; it is not real customer or account data.

## Features

- Reproducible 24-month synthetic transactions with stable IDs, multiple
  simulated income sources, recurring bills, and realistic payment methods.
- Shared CSV validation and cleaning with field aliases, positive amount
  semantics, duplicate rules, and row-level removal summaries.
- Streamlit dashboard with date/category/type/payment filters, INR KPIs,
  spending charts, cash-flow trends, budgets, insights, and data-quality detail.
- Responsive FinTech design system with source-status badges, local refresh
  timestamp, same-duration KPI comparisons, Indian digit grouping, and filter reset.
- Interactive Plotly cash-flow, expense, category, payment, weekday/category
  heatmap, budget utilization, and anomaly-review charts.
- Transaction search, sorting, pagination, and CSV export.
- Session-only transaction entry. New entries are not persisted to disk/database.
- Locally configured JSON budgets; a starter set is used until custom budgets
  are saved.
- Rule-based recurring-cost analysis, category IQR anomaly flags, and a labeled
  moving-average baseline. The latter is a simple descriptive estimate, not a
  trained prediction model.
- Independent pytest coverage for data generation, cleaning, analytics, and
  budget configuration.

## Architecture and data flow

```text
generate_data.py
      │
      ▼
data/raw/transactions.csv ──► main.py / data_cleaning.py
                                      │
                                      ▼
                         data/processed/transactions_cleaned.csv
                                      │
                   ┌──────────────────┴───────────────────┐
                   ▼                                      ▼
             app.py dashboard                  visualization.py charts
```

| Path | Responsibility |
| --- | --- |
| `src/expense_tracker/data_generator.py` | Deterministic synthetic-data API |
| `src/expense_tracker/data_cleaning.py` | CSV schema aliases, validation, cleaning, quality summary |
| `src/expense_tracker/analytics.py` | Metrics, monthly/category/payment/weekday analysis, budgets, recurrence, IQR outliers |
| `src/expense_tracker/insights.py` | Explainable insight bundle |
| `src/expense_tracker/forecasting.py` | Transparent trailing-average expense baseline |
| `src/expense_tracker/budgets.py` | Validated local JSON budget storage |
| `app.py` | Interactive dashboard; uploads stay in memory |
| `main.py` | CLI preprocessing and printed data-quality/financial summaries |
| `src/visualization.py` | Backward-compatible static chart output |
| `tests/` | Automated unit tests independent of the Streamlit UI |

## Dashboard preview

Genuine screenshots captured from the running local dashboard are saved under
[`assets/screenshots/`](assets/screenshots/):

| Overview | Spending analytics |
| --- | --- |
| ![Expense Intelligence overview](assets/screenshots/overview.png) | ![Spending analytics charts](assets/screenshots/spending-analytics.png) |

| Budget intelligence | Transaction explorer |
| --- | --- |
| ![Budget utilization](assets/screenshots/budget-intelligence.png) | ![Transaction explorer](assets/screenshots/transaction-explorer.png) |

The app uses midnight navy surfaces with teal, cyan, violet, emerald, amber,
and coral accents. It is a local analytics dashboard; no live bank connection
is implied.

The existing `data/expenses.csv`, `data/cleaned_expenses.csv`, and
`data/expenses_case2.csv` remain available as legacy examples. If the new
generated raw file is absent, the CLI/dashboard can fall back to
`data/expenses.csv` or `data/cleaned_expenses.csv` as appropriate.

## Dataset schema

| Column | Meaning |
| --- | --- |
| `Transaction_ID` | Unique stable simulated transaction identifier |
| `Date` | Calendar transaction date |
| `Category` | Income source or spending category |
| `Description` | Simulated transaction description |
| `Amount` | Positive currency magnitude; `Type` determines direction |
| `Type` | `Income` or `Expense` |
| `Payment_Method` | Simulated payment method |
| `Month`, `Month_Num`, `Weekday` | Derived during cleaning |

The default generator creates 1,920 rows (80/month) over 24 calendar months,
starting January 2024. Pass a seed to `generate_transactions()` to reproduce an
identical dataset. All values are simulated; no personal financial information
is included.

## Cleaning and validation rules

- Required fields are `Date`, `Category`, `Amount`, and `Type`; supported
  aliases include `transaction_date`, `transaction_type`, `value`, and
  `payment_mode`.
- Headers are canonicalized before checking the schema. Conflicting aliases
  that map to one canonical name are rejected.
- Dates and numeric amounts are parsed with invalid values removed and counted.
- Transaction types accept common labels such as debit/credit and outflow/inflow.
- Category labels are trimmed and title-cased; missing descriptions and payment
  methods are optional (`Unknown` for a missing payment method).
- Exact duplicate rows are removed first. If a transaction ID is present,
  repeated non-empty IDs are removed after the first occurrence.
- Zero, negative, and non-numeric amounts are invalid. Amounts are positive
  magnitudes; income and expenses are distinguished by `Type`.
- The data-quality report shows input/valid/removed row counts, categorized
  removal reasons, and original missing-value counts. Inputs are not overwritten.

## Analytics methodology

- **Savings rate:** `(income − expenses) / income × 100`; defined as 0% when
  income is zero. A negative rate means expenses exceed income.
- **Recurring expenses:** same category and description, amounts within 5% of
  the group median (minimum ₹10), and at least three distinct calendar months.
  This is a heuristic, not a confirmed subscription.
- **Unusual expenses:** high values above the per-category `Q3 + 1.5 × IQR`
  fence. Categories with fewer than four observations are omitted.
- **Budget utilization:** filtered category spending divided by its monthly
  budget multiplied by the number of selected calendar months.
- **Expense baseline:** mean expense value for the trailing three observed
  calendar months, shown only when at least three months are available. It is
  descriptive rather than a fitted forecasting model and has no confidence
  interval.
- All dashboard sections share the same date, category, type, and payment
  filters. Amount calculations use positive magnitudes with transaction type
  controlling cash-flow direction.

## Installation and execution (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python generate_data.py
python main.py
streamlit run app.py --server.port 8502
```

If PowerShell blocks virtual-environment activation, use the interpreter
directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe generate_data.py
.\venv\Scripts\python.exe main.py
.\venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

Run the legacy generator with `python src/generate_data.py`; it writes the same
canonical raw dataset. Static charts can be refreshed with
`python visualization.py` after preprocessing.

Run automated tests:

```powershell
python -m pytest -q
```

## Budgets, uploads, and privacy

- Monthly budgets are saved locally at `data/budgets.json` after a user edits
  them; this file is ignored by Git. If absent, the dashboard displays clearly
  labeled recommended starter values.
- The transaction-entry form keeps records in Streamlit session state only.
  Entries disappear when that session is cleared; no database persistence is
  provided.
- Uploaded CSVs are read and cleaned in memory. The app does not save or
  overwrite the uploaded file. Export is an explicit user-triggered download.
- Use only synthetic or appropriately authorized data. This local prototype is
  not a bank integration, tax tool, financial advisor, or production-grade
  secure data platform.

## Limitations and next steps

This is a single-user local analytics prototype. It has no authentication,
multi-user storage, bank integration, transaction reconciliation, or validated
machine-learning forecast. Budget starter values are examples and should be
customized. Anomaly and recurring-payment results are explainable heuristics
that may produce false positives/negatives. See
[`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md) and
[`docs/PHASE_1_REPORT.md`](docs/PHASE_1_REPORT.md) for audit and implementation
details.
