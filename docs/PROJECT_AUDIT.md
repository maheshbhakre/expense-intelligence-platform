# Project Audit

## Scope and baseline

The repository initially contained a Streamlit dashboard (`app.py`), a
preprocessing script (`main.py`), scripts under `src/`, three CSV datasets,
saved charts, a README, and a requirements file. The worktree was clean at the
start of Phase 1. The existing Python 3.10 virtual environment includes
Streamlit, Pandas, NumPy, Plotly, Matplotlib, and Seaborn; pytest was not
present in the initial dependency list.

The checked-in datasets contain 300 rows (`expenses.csv` and
`cleaned_expenses.csv`) and 30 rows (`expenses_case2.csv`). The 300-row data
covers 2024-01-01 through 2024-04-29. Their observed rows had no exact
duplicates, invalid dates, invalid numeric amounts, or negative amounts.

## Findings

### High priority

1. **Insufficient data volume and time coverage.** The generator creates only
   300 transactions over about four months. This is inadequate for stable
   monthly comparisons, recurring-cost rules, or useful forecast baselines.
2. **Input cleaning is inconsistent and incomplete.** `main.py` drops some
   nulls before converting dates and amounts, so invalid non-null values can
   survive as `NaT`/`NaN`. It does not validate transaction types, negative
   values, aliases, or missing columns and does not report why rows were
   removed.
3. **Dashboard upload parsing bypasses the cleaning workflow.** The app
   directly parses uploaded data and validates only four exact column names.
   Malformed CSVs and common header aliases do not get actionable feedback.
4. **KPI filters are inconsistent.** The original KPIs are calculated before
   category filtering, and the monthly chart includes both income and
   expenses while appearing as a spending trend. Negative balances and savings
   rate are not handled explicitly.

### Medium priority

5. **No reusable analytics, budgets, anomaly methods, or tests.** Most logic
   resides directly in scripts and the dashboard. There is no pytest suite or
   documented statistical methodology.
6. **The generator is not fully reproducible as a callable API.** It seeds
   NumPy's process-global random state and writes relative to the current
   directory; synthetic records lack stable transaction identifiers.
7. **Static chart generation is brittle.** It assumes a previously generated
   cleaned CSV and month-number column, and does not handle empty or malformed
   inputs explicitly.
8. **Dependency metadata is an oversized environment snapshot.** The
   requirements file pins many transitive packages that the application does
   not import, while omitting test tooling and clear direct-dependency intent.

### Low priority

9. **Documentation and UI are prototype-oriented.** The README describes
   future work as if some capabilities already exist; the dashboard has a
   minimal layout and no dedicated data-quality or transaction-explorer view.
10. **Data handling boundaries are unclear.** The original app has no local
    budget configuration or clear statement about upload/session persistence.

## Prioritized implementation plan

1. Introduce a deterministic 24-month synthetic-data generator and a reusable,
   transparent CSV normalization/validation/cleaning module; retain the
   existing script entry points and input/output paths as compatibility
   fallbacks.
2. Add independently testable analytics, explainable insights, recurring-cost
   and IQR anomaly detection, budget utilities, and a clearly labeled
   descriptive moving-average forecast.
3. Rebuild the Streamlit app around reusable cleaned data, consistent global
   filters, INR formatting, quality reporting, local JSON budgets, CSV export,
   and session-only transaction entry.
4. Add automated tests, configure the local dashboard, simplify direct
   dependencies, and update the runbook and privacy/methodology documentation.
5. Execute the test suite, verify entry points/imports, regenerate the
   reproducible dataset and charts, and launch/check the app on port 8502 or
   the next available port.
