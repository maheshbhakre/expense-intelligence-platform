import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Expense Tracker", layout="wide")

st.title("💰 Expense Tracker Dashboard")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader("📂 Upload your Expense CSV", type=["csv"])

# -----------------------------
# BUTTON CONTROL
# -----------------------------
show_result = st.button("🚀 Show Results")

# -----------------------------
# PROCESS ONLY AFTER BUTTON
# -----------------------------
if show_result:

    # Load data
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("CSV Uploaded Successfully ✅")
    else:
        df = pd.read_csv("data/cleaned_expenses.csv")
        st.info("Using default dataset")

    # -----------------------------
    # CLEAN DATA
    # -----------------------------
    df.columns = df.columns.str.strip()

    required_cols = ["Date", "Category", "Amount", "Type"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            st.stop()

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    df.dropna(subset=['Date', 'Amount'], inplace=True)

    if df.empty:
        st.error("No valid data ❌")
        st.stop()

    # -----------------------------
    # KPI CALCULATIONS
    # -----------------------------
    total_expense = df[df['Type'] == 'Expense']['Amount'].sum()
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    balance = total_income - total_expense

    # -----------------------------
    # KPIs (VISIBLE AFTER BUTTON)
    # -----------------------------
    st.subheader("📊 Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("💸 Total Expense", f"₹{total_expense:,.0f}")
    col2.metric("💰 Total Income", f"₹{total_income:,.0f}")
    col3.metric("📊 Balance", f"₹{balance:,.0f}")

    st.markdown("---")

    # -----------------------------
    # FILTERS
    # -----------------------------
    st.sidebar.header("Filters")

    categories = st.sidebar.multiselect(
        "Category",
        options=df['Category'].unique(),
        default=list(df['Category'].unique())
    )

    if categories:
        df = df[df['Category'].isin(categories)]

    # -----------------------------
    # CHARTS
    # -----------------------------
    expense_df = df[df['Type'] == 'Expense']

    # Category Chart
    category_data = expense_df.groupby('Category')['Amount'].sum().reset_index()

    fig1 = px.bar(
        category_data,
        x='Category',
        y='Amount',
        color='Category',
        title="Category-wise Spending",
        template="plotly_dark"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Pie Chart
    fig2 = px.pie(
        category_data,
        names='Category',
        values='Amount',
        title="Expense Distribution",
        template="plotly_dark"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Monthly Trend
    df['Month'] = df['Date'].dt.to_period("M").astype(str)
    monthly = df.groupby('Month')['Amount'].sum().reset_index()

    fig3 = px.line(
        monthly,
        x='Month',
        y='Amount',
        markers=True,
        title="Monthly Trend",
        template="plotly_dark"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # INSIGHTS
    # -----------------------------
    st.subheader("💡 Insights")

    if not category_data.empty:
        top = category_data.sort_values(by='Amount', ascending=False).iloc[0]

        st.write(f"👉 Highest spending: **{top['Category']} (₹{top['Amount']})**")

        if top['Amount'] > 0.3 * total_expense:
            st.warning("⚠️ Overspending detected!")

    if balance < 0:
        st.error("🚨 Expenses > Income")
    else:
        st.success("✅ Financial balance is good")

    # -----------------------------
    # RAW DATA
    # -----------------------------
    if st.checkbox("Show Data"):
        st.dataframe(df)

# -----------------------------
# DEFAULT MESSAGE
# -----------------------------
else:
    st.info("👆 Upload CSV and click 'Show Results'")