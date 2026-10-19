"""Streamlit dashboard for financial summaries, budgets, and transaction data."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.expense_tracker.analytics import (
    budget_utilization,
    category_spending,
    detect_unusual_transactions,
    month_over_month_spending,
    monthly_cash_flow,
    payment_method_analysis,
    recurring_expenses,
    summarize_transactions,
    weekday_analysis,
    weekday_category_heatmap,
)
from src.expense_tracker.budgets import (
    DEFAULT_MONTHLY_BUDGETS,
    load_budgets,
    save_budgets,
)
from src.expense_tracker.data_cleaning import clean_transactions, read_transactions
from src.expense_tracker.forecasting import forecast_next_month_expenses
from src.expense_tracker.insights import build_spending_insights
from src.expense_tracker.ui import (
    KPI_COLORS,
    THEME,
    comparison_text,
    format_inr,
    inject_design_system,
    render_hero,
    render_kpis,
    style_chart,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_CANDIDATES = (
    ROOT / "data" / "raw" / "transactions.csv",
    ROOT / "data" / "expenses.csv",
)
PALETTE = {
    "income": THEME["positive"],
    "expense": THEME["negative"],
    "balance": THEME["cyan"],
    "teal": THEME["teal"],
    "cyan": THEME["cyan"],
    "violet": THEME["violet"],
    "positive": THEME["positive"],
    "negative": THEME["negative"],
    "warning": THEME["warning"],
    "muted": THEME["muted"],
}

st.set_page_config(
    page_title="Expense Tracker | Financial Intelligence",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_design_system()


@st.cache_data(show_spinner="Validating and cleaning transactions...")
def _load_and_clean(
    file_content: bytes | None, default_file: str
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Cache normalized data by its uploaded contents or source path."""
    raw = read_transactions(file_content if file_content is not None else default_file)
    return clean_transactions(raw)


@st.cache_data(show_spinner=False)
def _calculate_analytics(
    frame: pd.DataFrame, budgets: dict[str, float], months_in_scope: int
) -> dict[str, object]:
    """Cache filtered analytics shared by dashboard sections."""
    return {
        "summary": summarize_transactions(frame),
        "categories": category_spending(frame),
        "monthly": monthly_cash_flow(frame),
        "budgets": budget_utilization(frame, budgets, months_in_scope),
        "month_changes": month_over_month_spending(frame),
        "recurring": recurring_expenses(frame),
        "unusual": detect_unusual_transactions(frame),
        "weekdays": weekday_analysis(frame),
        "weekday_heatmap": weekday_category_heatmap(frame),
        "payment_methods": payment_method_analysis(frame),
        "forecast": forecast_next_month_expenses(frame),
        "insights": build_spending_insights(frame),
    }


def _money(value: float | int) -> str:
    """Format currency amounts consistently in Indian rupees."""
    return format_inr(value)


def _comparison_values(
    current: dict[str, float | int], previous: dict[str, float | int]
) -> list[tuple[str, str, str, str, str]]:
    """Build actual same-duration prior-period comparisons for dashboard KPIs."""
    has_previous_data = previous["transaction_count"] > 0
    amount_comparison = lambda key: (
        comparison_text(float(current[key]), float(previous[key]))
        if has_previous_data
        else "N/A vs prior period"
    )
    return [
        (
            "Total Income",
            _money(current["total_income"]),
            amount_comparison("total_income"),
            "Income in the selected date, category, type, and payment filters.",
            KPI_COLORS[0],
        ),
        (
            "Total Expenses",
            _money(current["total_expenses"]),
            amount_comparison("total_expenses"),
            "Expenses in the selected date, category, type, and payment filters.",
            KPI_COLORS[1],
        ),
        (
            "Net Balance",
            _money(current["net_balance"]),
            (
                f"{'+' if current['net_balance'] - previous['net_balance'] >= 0 else '-'}"
                f"{_money(abs(current['net_balance'] - previous['net_balance']))} vs prior period"
                if has_previous_data
                else "N/A vs prior period"
            ),
            "Net balance is income minus expenses. Delta is the actual rupee change.",
            KPI_COLORS[2],
        ),
        (
            "Savings Rate",
            f"{current['savings_rate']:.1f}%",
            comparison_text(
                float(current["savings_rate"]),
                float(previous["savings_rate"]),
                percentage_points=True,
            )
            if has_previous_data
            else "N/A vs prior period",
            "Savings rate is (income minus expenses) divided by income.",
            KPI_COLORS[3],
        ),
        (
            "Transactions",
            f"{current['transaction_count']:,}",
            comparison_text(
                float(current["transaction_count"]),
                float(previous["transaction_count"]),
            )
            if previous["transaction_count"] > 0
            else "N/A vs prior period",
            "Number of valid transactions in the selected filters.",
            KPI_COLORS[4],
        ),
    ]


def _style_money_chart(figure: object, axis: str = "y", height: int = 370) -> object:
    """Apply common Plotly styling and rupee axis formatting."""
    return style_chart(figure, currency_axis=axis, height=height)


def _render_empty_state(message: str) -> None:
    st.info(message)


def _source_file() -> Path | None:
    return next((path for path in DEFAULT_DATA_CANDIDATES if path.exists()), None)


def _month_count(start: date, end: date) -> int:
    return max((end.year - start.year) * 12 + end.month - start.month + 1, 1)


def _append_session_entries(frame: pd.DataFrame) -> pd.DataFrame:
    entries = st.session_state.get("session_entries", [])
    if not entries:
        return frame.copy()
    added, _ = clean_transactions(pd.DataFrame.from_records(entries))
    return pd.concat([frame, added], ignore_index=True, sort=False)


def _render_budget_editor(categories: list[str], budgets: dict[str, float]) -> None:
    st.markdown("#### Monthly category budgets")
    st.caption(
        "Budgets are stored locally in `data/budgets.json`. Recommended starter "
        "limits are shown until you save custom settings."
    )
    with st.form("budget_editor", clear_on_submit=True):
        category = st.text_input("Category", placeholder="e.g. Groceries")
        amount = st.number_input(
            "Monthly limit (₹)", min_value=1.0, value=5_000.0, step=500.0
        )
        submitted = st.form_submit_button("Save or update budget")
    if submitted:
        normalized = category.strip().title()
        if not normalized:
            st.error("Enter a category name before saving a budget.")
        else:
            updated = dict(budgets)
            updated[normalized] = float(amount)
            try:
                save_budgets(updated, ROOT / "data" / "budgets.json")
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(f"Saved a monthly budget for {normalized}.")
                st.rerun()

    if budgets:
        with st.form("budget_removal"):
            remove_category = st.selectbox("Remove a budget", sorted(budgets))
            remove_submitted = st.form_submit_button("Remove selected budget")
        if remove_submitted:
            updated = {key: value for key, value in budgets.items() if key != remove_category}
            try:
                save_budgets(updated, ROOT / "data" / "budgets.json")
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success(f"Removed the {remove_category} budget.")
                st.rerun()

    if st.button("Reset to recommended defaults", key="reset_budgets"):
        try:
            save_budgets(dict(DEFAULT_MONTHLY_BUDGETS), ROOT / "data" / "budgets.json")
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success("Budgets reset to the documented starter values.")
            st.rerun()
    if categories:
        st.caption("Categories in this dataset: " + ", ".join(categories))


def _render_transaction_entry(start_date: date, end_date: date) -> None:
    st.markdown("#### Add a transaction to this session")
    st.caption(
        "Entries are kept in this browser session only and are not written to a "
        "file or database."
    )
    with st.form("transaction_entry", clear_on_submit=True):
        columns = st.columns(3)
        default_date = min(max(date.today(), start_date), end_date)
        entry_date = columns[0].date_input("Date", value=default_date)
        entry_type = columns[1].selectbox("Type", ["Expense", "Income"])
        entry_amount = columns[2].number_input(
            "Amount (₹)", min_value=0.0, value=0.0, step=100.0
        )
        category = st.text_input("Category", placeholder="e.g. Groceries or Salary")
        description = st.text_input("Description")
        payment_method = st.selectbox(
            "Payment method", ["UPI", "Card", "Cash", "Bank Transfer", "Auto-debit", "Other"]
        )
        submitted = st.form_submit_button("Add to this session")
    if submitted:
        category_value = category.strip().title()
        if not category_value:
            st.error("Enter a category for this transaction.")
        elif entry_amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            entries = st.session_state.setdefault("session_entries", [])
            entries.append(
                {
                    "Transaction_ID": f"SESSION-{len(entries) + 1:04d}",
                    "Date": entry_date.isoformat(),
                    "Category": category_value,
                    "Description": description.strip() or "Session entry",
                    "Amount": float(entry_amount),
                    "Type": entry_type,
                    "Payment_Method": payment_method,
                }
            )
            st.success("Transaction added to the current session.")
            st.rerun()


with st.sidebar:
    st.header("Workspace")
    uploaded = st.file_uploader(
        "Upload a transaction CSV",
        type=["csv"],
        help="The uploaded file is processed in memory and is not saved to disk.",
    )
    default_path = _source_file()
    if uploaded is not None:
        filter_identity = hashlib.sha256(uploaded.getvalue()).hexdigest()[:12]
    elif default_path is not None:
        file_stat = default_path.stat()
        filter_identity = hashlib.sha256(
            f"{default_path}:{file_stat.st_mtime_ns}:{file_stat.st_size}".encode()
        ).hexdigest()[:12]
    else:
        filter_identity = "empty"
    if uploaded is None and default_path is None:
        st.warning("No default dataset found. Generate one with `python generate_data.py`.")
    elif uploaded is None:
        st.caption(f"Using local simulated data: `{default_path.relative_to(ROOT)}`")

    if st.button("↻ Refresh data", key="refresh_data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("_last_successful_load", None)
        st.rerun()

    st.divider()
    st.header("Filters")
    if st.button("Reset filters", key="reset_filters", use_container_width=True):
        for name in ("date_filter", "category_filter", "type_filter", "payment_filter"):
            key = f"{name}_{filter_identity}"
            st.session_state.pop(key, None)
        st.rerun()

source_path = default_path if uploaded is None else None
if uploaded is not None:
    source_label = f"Uploaded file: {uploaded.name}"
    file_content: bytes | None = uploaded.getvalue()
elif source_path is not None:
    source_label = f"Local dataset: {source_path.relative_to(ROOT)}"
    file_content = None
else:
    source_label = "No dataset"
    file_content = None

if source_path is None and uploaded is None:
    st.info("Create the reproducible sample dataset or upload a CSV to begin.")
    st.stop()

try:
    source_data, quality = _load_and_clean(
        file_content, str(source_path) if source_path is not None else ""
    )
except ValueError as exc:
    st.error(f"Could not load transaction data: {exc}")
    st.stop()

if (
    "_last_successful_load" not in st.session_state
    or st.session_state.get("_last_loaded_source") != filter_identity
):
    st.session_state["_last_successful_load"] = datetime.now().astimezone().strftime(
        "%b %d, %Y · %I:%M:%S %p %Z"
    )
    st.session_state["_last_loaded_source"] = filter_identity

simulated_data = uploaded is None
combined_data = _append_session_entries(source_data)
if combined_data.empty:
    st.warning("No valid transactions were found. Review the Data Quality tab for removal reasons.")

if not combined_data.empty:
    minimum_date = combined_data["Date"].min().date()
    maximum_date = combined_data["Date"].max().date()
    with st.sidebar:
        selected_dates = st.date_input(
            "Transaction date range",
            value=(minimum_date, maximum_date),
            min_value=minimum_date,
            max_value=maximum_date,
            key=f"date_filter_{filter_identity}",
        )
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date = end_date = selected_dates
        selected_categories = st.multiselect(
            "Category",
            options=sorted(combined_data["Category"].dropna().unique().tolist()),
            default=sorted(combined_data["Category"].dropna().unique().tolist()),
            key=f"category_filter_{filter_identity}",
        )
        selected_types = st.multiselect(
            "Transaction type",
            options=["Expense", "Income"],
            default=["Expense", "Income"],
            key=f"type_filter_{filter_identity}",
        )
        payment_options = sorted(combined_data["Payment_Method"].dropna().unique().tolist())
        selected_payments = st.multiselect(
            "Payment method",
            options=payment_options,
            default=payment_options,
            key=f"payment_filter_{filter_identity}",
        )

    filtered = combined_data[
        combined_data["Date"].dt.date.between(start_date, end_date)
        & combined_data["Category"].isin(selected_categories)
        & combined_data["Type"].isin(selected_types)
        & combined_data["Payment_Method"].isin(selected_payments)
    ].copy()
else:
    start_date = end_date = date.today()
    selected_categories = []
    selected_types = []
    selected_payments = []
    filtered = combined_data.copy()

previous_duration = (end_date - start_date).days + 1
previous_start = start_date - timedelta(days=previous_duration)
previous_end = start_date - timedelta(days=1)
previous_filtered = combined_data[
    combined_data["Date"].dt.date.between(previous_start, previous_end)
    & combined_data["Category"].isin(selected_categories)
    & combined_data["Type"].isin(selected_types)
    & combined_data["Payment_Method"].isin(selected_payments)
].copy()

budgets: dict[str, float] = {}
try:
    budgets = load_budgets(ROOT / "data" / "budgets.json")
except ValueError as exc:
    st.error(f"Budget settings issue: {exc}")

display_data = filtered
period_months = _month_count(start_date, end_date)
analytics = _calculate_analytics(display_data, budgets, period_months)
summary = analytics["summary"]
previous_summary = summarize_transactions(previous_filtered)

render_hero(
    "·".join(
        ["Uploaded CSV" if uploaded is not None else "Local dataset"]
        + ([uploaded.name] if uploaded is not None else [])
    ),
    simulated=simulated_data,
    refreshed_at=st.session_state["_last_successful_load"],
    session_entry_count=len(st.session_state.get("session_entries", [])),
)

tabs = st.tabs(
    [
        "Executive Overview",
        "Spending Analytics",
        "Financial Trends",
        "Budget Management",
        "Transaction Explorer",
        "Spending Insights",
        "Data Quality",
    ]
)

with tabs[0]:
    st.markdown('<div class="et-section-title">Executive overview</div>', unsafe_allow_html=True)
    st.caption(f"Filtered cash flow · {start_date:%d %b %Y} — {end_date:%d %b %Y}")
    render_kpis(_comparison_values(summary, previous_summary))
    st.caption(
        "Comparisons use the immediately preceding date window of equal length "
        "and identical category, type, and payment filters. N/A means no comparable baseline."
    )
    if display_data.empty:
        _render_empty_state("No transactions match the selected filters. Adjust or reset the filters.")
    else:
        left, right = st.columns([1.45, 1], gap="large")
        monthly = analytics["monthly"]
        with left:
            st.markdown("#### Monthly cash flow")
            if not monthly.empty:
                overview_monthly = monthly.melt(
                    id_vars="Month",
                    value_vars=["Income", "Expenses"],
                    var_name="Type",
                    value_name="Amount",
                )
                figure = px.line(
                    overview_monthly,
                    x="Month",
                    y="Amount",
                    color="Type",
                    markers=True,
                    color_discrete_map={
                        "Income": PALETTE["income"],
                        "Expenses": PALETTE["expense"],
                    },
                    labels={"Amount": "Amount (INR)", "Month": "Month"},
                    hover_data={"Amount": ":,.0f"},
                )
                st.plotly_chart(_style_money_chart(figure, height=360), width="stretch")
        with right:
            st.markdown("#### Spending by category")
            categories = analytics["categories"]
            if categories.empty:
                _render_empty_state("No expenses in the selected period.")
            else:
                ranking = categories.head(8).sort_values("Amount", ascending=True)
                figure = px.bar(
                    ranking,
                    x="Amount",
                    y="Category",
                    orientation="h",
                    color="Category",
                    color_discrete_sequence=[PALETTE["teal"], PALETTE["cyan"], PALETTE["violet"]],
                    hover_data={"Amount": ":,.0f", "Percentage": ":.1f"},
                    labels={"Amount": "Expenses (INR)", "Percentage": "Share (%)"},
                )
                figure.update_layout(showlegend=False)
                st.plotly_chart(_style_money_chart(figure, axis="x", height=360), width="stretch")
        st.markdown("#### Recent activity")
        recent = display_data.sort_values("Date", ascending=False).head(8)
        st.dataframe(
            recent[["Date", "Category", "Type", "Amount", "Payment_Method"]],
            hide_index=True,
            width="stretch",
            column_config={
                "Amount": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f")
            },
        )
        st.caption(
            f"Net cash flow for the selected filters: **{_money(summary['net_balance'])}**"
        )

with tabs[1]:
    st.markdown('<div class="et-section-title">Spending analytics</div>', unsafe_allow_html=True)
    st.caption("Explore where money goes and how payment behavior varies.")
    categories = analytics["categories"]
    if categories.empty:
        _render_empty_state("No expense transactions match the current filters.")
    else:
        left, right = st.columns(2)
        with left:
            st.markdown("#### Category ranking")
            ranked = categories.sort_values("Amount", ascending=True)
            figure = px.bar(
                ranked,
                x="Amount",
                y="Category",
                orientation="h",
                color="Category",
                hover_data={"Amount": ":,.0f", "Percentage": ":.1f"},
                labels={"Amount": "Expense (INR)", "Percentage": "Share (%)"},
                color_discrete_sequence=[PALETTE["teal"], PALETTE["cyan"], PALETTE["violet"]],
            )
            figure.update_layout(showlegend=False)
            st.plotly_chart(_style_money_chart(figure, axis="x", height=max(330, 34 * len(ranked))), width="stretch")
        with right:
            st.markdown("#### Expense distribution")
            figure = px.pie(
                categories,
                names="Category",
                values="Amount",
                hole=0.48,
                hover_data=["Percentage"],
                color_discrete_sequence=[
                    PALETTE["teal"], PALETTE["cyan"], PALETTE["violet"],
                    PALETTE["positive"], "#FBBF24", "#FB7185",
                ],
            )
            st.plotly_chart(style_chart(figure, currency_axis=None, height=370), width="stretch")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Category × weekday spending")
        heatmap = analytics["weekday_heatmap"]
        if heatmap.empty or heatmap["Category"].nunique() < 2 or heatmap["Weekday"].nunique() < 2:
            _render_empty_state(
                "A weekday heatmap appears when at least two spending categories "
                "and two weekdays are present in the filtered data."
            )
        else:
            figure = px.density_heatmap(
                heatmap,
                x="Weekday",
                y="Category",
                z="Amount",
                histfunc="sum",
                color_continuous_scale=["#182338", PALETTE["cyan"], PALETTE["teal"]],
                labels={"Amount": "Expenses (INR)"},
                hover_data={"Amount": ":,.0f"},
            )
            figure.update_layout(coloraxis_colorbar={"title": "₹"})
            st.plotly_chart(style_chart(figure, currency_axis=None, height=390), width="stretch")
    with right:
        st.markdown("#### Payment methods")
        payment_data = analytics["payment_methods"]
        if payment_data.empty:
            _render_empty_state("No transactions available for payment-method analysis.")
        else:
            figure = px.bar(
                payment_data,
                x="Payment_Method",
                y="Amount",
                color="Type",
                barmode="group",
                color_discrete_map={"Income": PALETTE["income"], "Expense": PALETTE["expense"]},
                hover_data={"Amount": ":,.0f", "Transactions": True},
                labels={"Amount": "Amount (INR)", "Payment_Method": "Payment method"},
            )
            st.plotly_chart(_style_money_chart(figure, height=390), width="stretch")
            st.dataframe(payment_data, hide_index=True, width="stretch")

with tabs[2]:
    st.markdown('<div class="et-section-title">Financial trends</div>', unsafe_allow_html=True)
    st.caption("Historical monthly totals derived from the currently filtered transaction dates.")
    monthly = analytics["monthly"]
    if monthly.empty:
        _render_empty_state("No transactions match the current filters.")
    else:
        st.markdown("#### Monthly income vs expenses")
        long_monthly = monthly.melt(
            id_vars="Month", value_vars=["Income", "Expenses"],
            var_name="Type", value_name="Amount",
        )
        figure = px.line(
            long_monthly,
            x="Month",
            y="Amount",
            color="Type",
            markers=True,
            color_discrete_map={"Income": PALETTE["income"], "Expenses": PALETTE["expense"]},
            labels={"Amount": "Amount (INR)"},
            hover_data={"Amount": ":,.0f"},
        )
        st.plotly_chart(_style_money_chart(figure), width="stretch")
        st.markdown("#### Monthly expense trend")
        expenses_figure = px.area(
            monthly,
            x="Month",
            y="Expenses",
            markers=True,
            color_discrete_sequence=[PALETTE["teal"]],
            labels={"Expenses": "Expenses (INR)"},
            hover_data={"Expenses": ":,.0f"},
        )
        expenses_figure.update_traces(line={"color": PALETTE["teal"]}, fillcolor="rgba(45,226,197,.08)")
        st.plotly_chart(_style_money_chart(expenses_figure), width="stretch")
        st.markdown("#### Net cash flow")
        figure = px.bar(
            monthly,
            x="Month",
            y="Net_Cash_Flow",
            color="Net_Cash_Flow",
            color_continuous_scale=[PALETTE["negative"], PALETTE["positive"]],
            labels={"Net_Cash_Flow": "Net cash flow (INR)"},
            hover_data={"Net_Cash_Flow": ":,.0f"},
        )
        st.plotly_chart(_style_money_chart(figure), width="stretch")
        with st.expander("View monthly cash-flow table"):
            st.dataframe(monthly, hide_index=True, width="stretch")
    forecast = analytics["forecast"]
    st.markdown("#### Descriptive next-month estimate")
    if forecast.empty:
        st.info("At least three calendar months are needed for the moving-average baseline.")
    else:
        estimate = forecast.iloc[0]
        st.metric(
            f"Historical baseline estimate · {estimate['Month']}",
            _money(estimate["Forecast_Expenses"]),
        )
        st.caption(
            f"ESTIMATE, NOT A PREDICTION · {estimate['Method']}; "
            "no model training or confidence interval is used."
        )
        if not monthly.empty:
            historical = monthly.tail(6)
            figure = go.Figure()
            figure.add_trace(
                go.Scatter(
                    x=historical["Month"],
                    y=historical["Expenses"],
                    mode="lines+markers",
                    name="Historical expenses",
                    line={"color": PALETTE["cyan"], "width": 2},
                )
            )
            figure.add_trace(
                go.Scatter(
                    x=[historical["Month"].iloc[-1], estimate["Month"]],
                    y=[historical["Expenses"].iloc[-1], estimate["Forecast_Expenses"]],
                    mode="lines+markers",
                    name="Moving-average estimate",
                    line={"color": PALETTE["violet"], "width": 2, "dash": "dash"},
                    marker={"symbol": ["circle", "diamond"], "size": [7, 11]},
                )
            )
            figure.update_layout(xaxis_title="Month", yaxis_title="Expenses (INR)")
            st.plotly_chart(_style_money_chart(figure), width="stretch")
    changes = analytics["month_changes"]
    if not changes.empty:
        st.markdown("#### Month-over-month expense change")
        changes_chart = changes.dropna(subset=["Change"])
        if not changes_chart.empty:
            figure = px.bar(
                changes_chart,
                x="Month",
                y="Change",
                color="Change",
                color_continuous_scale=[PALETTE["negative"], THEME["grid"], PALETTE["positive"]],
                hover_data={"Change": ":,.0f", "Change_Percent": ":.1f"},
                labels={"Change": "Change vs previous month (INR)"},
            )
            st.plotly_chart(_style_money_chart(figure), width="stretch")
        with st.expander("View month-over-month details"):
            st.dataframe(changes, hide_index=True, width="stretch")

with tabs[3]:
    st.markdown('<div class="et-section-title">Budget intelligence</div>', unsafe_allow_html=True)
    st.caption("Compare filtered actual spending with your monthly limits.")
    _render_budget_editor(sorted(display_data["Category"].dropna().unique()), budgets)
    budget_data = analytics["budgets"]
    st.markdown(f"#### Budget utilization for the selected {period_months}-month window")
    st.caption("Monthly category limits are multiplied by the number of calendar months selected.")
    if budget_data.empty:
        _render_empty_state("No categories or budgets to compare.")
    else:
        configured = budget_data[budget_data["Period_Budget"] > 0].copy()
        if not configured.empty:
            plot_data = configured.melt(
                id_vars="Category",
                value_vars=["Spent", "Period_Budget"],
                var_name="Measure",
                value_name="Amount",
            )
            figure = px.bar(
                plot_data,
                x="Category",
                y="Amount",
                color="Measure",
                barmode="group",
                color_discrete_map={
                    "Spent": PALETTE["cyan"],
                    "Period_Budget": PALETTE["violet"],
                },
                labels={"Amount": "Amount (INR)", "Period_Budget": "Budget"},
                hover_data={"Amount": ":,.0f"},
            )
            st.plotly_chart(_style_money_chart(figure), width="stretch")
            utilization = configured.sort_values("Utilization_Percent", ascending=True)
            utilization_fig = px.bar(
                utilization,
                x="Utilization_Percent",
                y="Category",
                orientation="h",
                color="Over_Budget",
                color_discrete_map={
                    True: PALETTE["negative"],
                    False: PALETTE["positive"],
                },
                labels={"Utilization_Percent": "Budget used (%)", "Over_Budget": "Over budget"},
                hover_data={"Spent": ":,.0f", "Period_Budget": ":,.0f"},
            )
            utilization_fig.add_vline(x=100, line_dash="dash", line_color=PALETTE["warning"])
            utilization_fig.update_xaxes(ticksuffix="%", range=[0, max(110, float(utilization["Utilization_Percent"].max()) * 1.05)])
            st.plotly_chart(style_chart(utilization_fig, currency_axis=None), width="stretch")
        st.dataframe(
            budget_data.style.format(
                {
                    "Spent": "₹{:,.0f}",
                    "Monthly_Budget": "₹{:,.0f}",
                    "Period_Budget": "₹{:,.0f}",
                    "Utilization_Percent": "{:.1f}%",
                },
                na_rep="No budget",
            ),
            hide_index=True,
            width="stretch",
        )
        over = budget_data[budget_data["Over_Budget"]]
        if not over.empty:
            for row in over.itertuples():
                st.warning(
                    f"{row.Category} is over budget: spent {_money(row.Spent)} "
                    f"against a {_money(row.Period_Budget)} limit for this window."
                )
        else:
            st.success("No configured budget is exceeded in the selected window.")
    st.caption(
        "Starter budget values are examples, not personalized financial advice. "
        "Edit them to reflect your own limits."
    )

with tabs[4]:
    st.markdown('<div class="et-section-title">Transaction explorer</div>', unsafe_allow_html=True)
    st.caption(
        "Search, inspect, and export transactions matching the global filters. "
        "Sort by selecting a column header."
    )
    search = st.text_input(
        "Search visible transactions",
        placeholder="Search category, description, transaction ID, or payment method",
    )
    explorer = display_data.copy()
    if search.strip():
        searchable_columns = [
            column
            for column in ("Transaction_ID", "Category", "Description", "Payment_Method", "Type")
            if column in explorer
        ]
        match = explorer[searchable_columns].fillna("").astype(str).agg(" ".join, axis=1)
        explorer = explorer[match.str.contains(search.strip(), case=False, regex=False)]
    page_size = st.selectbox("Rows per page", [25, 50, 100], index=0)
    page_count = max((len(explorer) + page_size - 1) // page_size, 1)
    page_number = st.number_input("Page", min_value=1, max_value=page_count, value=1, step=1)
    start = (int(page_number) - 1) * page_size
    st.caption(f"Showing {min(start + 1, len(explorer)):,}–{min(start + page_size, len(explorer)):,} of {len(explorer):,} matching transactions.")
    st.dataframe(
        explorer.iloc[start : start + page_size],
        hide_index=True,
        width="stretch",
        column_config={"Amount": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f")},
    )
    st.download_button(
        "Download filtered transactions as CSV",
        data=explorer.to_csv(index=False).encode("utf-8"),
        file_name="filtered_transactions.csv",
        mime="text/csv",
        disabled=explorer.empty,
    )
    st.divider()
    _render_transaction_entry(start_date, end_date)
    if st.session_state.get("session_entries"):
        if st.button("Clear session-only entries"):
            st.session_state.session_entries = []
            st.rerun()

with tabs[5]:
    st.markdown('<div class="et-section-title">Spending intelligence</div>', unsafe_allow_html=True)
    top_category = analytics["insights"]["highest_spending_category"]
    if top_category is None:
        st.info("No expense transactions match the current filters.")
    else:
        st.info(
            f"Highest spending category: **{top_category['Category']}** "
            f"({_money(top_category['Amount'])}, {top_category['Percentage']:.1f}% "
            "of filtered expenses)."
        )
    change_data = analytics["month_changes"]
    meaningful_changes = change_data.dropna(subset=["Change_Percent"])
    if meaningful_changes.empty:
        st.caption("Month-over-month changes require consecutive observed periods and a non-zero prior-month value.")
    else:
        latest = meaningful_changes.iloc[-1]
        direction = "increased" if latest["Change"] > 0 else "decreased"
        st.write(
            f"Expenses {direction} by {abs(latest['Change_Percent']):.1f}% "
            f"({_money(abs(latest['Change']))}) in {latest['Month']} versus the prior month."
        )
    with st.expander("Potential recurring costs", expanded=True):
        recurring = analytics["recurring"]
        st.caption(
            "Rule-based: matching category and description, at least three active "
            "months, and amounts within 5% (minimum ₹10) of the group's median."
        )
        if recurring.empty:
            st.info("No costs matched the recurring-expense rule in the filtered period.")
        else:
            st.dataframe(recurring, hide_index=True, width="stretch")
    with st.expander("Unusual transaction candidates", expanded=True):
        unusual = analytics["unusual"].copy()
        st.caption(
            "Review candidates only—not confirmed fraud. An expense is flagged "
            "above its category Q3 + 1.5 × IQR upper fence; categories with fewer "
            "than four transactions are skipped."
        )
        if unusual.empty:
            st.info("No expenses exceeded the category-level IQR upper fence.")
        else:
            unusual["Detection_Reason"] = unusual.apply(
                lambda row: (
                    f"Amount {_money(row['Amount'])} exceeds the category "
                    f"IQR upper fence of {_money(row['IQR_Upper_Bound'])}."
                ),
                axis=1,
            )
            visible_columns = [
                column
                for column in (
                    "Date",
                    "Category",
                    "Description",
                    "Amount",
                    "IQR_Upper_Bound",
                    "Detection_Reason",
                )
                if column in unusual
            ]
            st.dataframe(
                unusual[visible_columns],
                hide_index=True,
                width="stretch",
                column_config={
                    "Amount": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f"),
                    "IQR_Upper_Bound": st.column_config.NumberColumn(
                        "Review threshold (₹)", format="₹ %.2f"
                    ),
                },
            )

with tabs[6]:
    st.markdown('<div class="et-section-title">Data quality & provenance</div>', unsafe_allow_html=True)
    st.write(f"**Source:** {source_label}")
    st.write(
        f"**Input rows:** {quality['input_rows']:,} · "
        f"**Valid rows:** {quality['valid_rows']:,} · "
        f"**Removed rows:** {quality['removed_rows']:,}"
    )
    if quality["removal_reasons"]:
        st.markdown("#### Removed-row reasons")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Reason": reason.replace("_", " ").title(), "Rows": count}
                    for reason, count in quality["removal_reasons"].items()
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.success("No rows were removed by cleaning.")
    if quality["missing_values"]:
        st.markdown("#### Missing values in the original input")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Column": column, "Missing values": count}
                    for column, count in quality["missing_values"].items()
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("The source had no blank/null values in its input columns.")
    st.write(f"**Rows matching current filters:** {len(filtered):,}")
    st.write(f"**Session-only rows added:** {len(st.session_state.get('session_entries', [])):,}")
    st.caption(
        "Uploads are parsed and cleaned in memory; the original uploaded file is "
        "never overwritten or stored by this app."
    )
