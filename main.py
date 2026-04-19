import pandas as pd
import os

# Ensure directories exist
os.makedirs("data", exist_ok=True)

# Load data
df = pd.read_csv("data/expenses.csv")

print("📌 Raw Data Preview:")
print(df.head())

# -------------------------------
# CLEANING
# -------------------------------
df.drop_duplicates(inplace=True)
df.dropna(subset=['Date', 'Amount', 'Category', 'Type'], inplace=True)

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

df['Category'] = df['Category'].str.strip().str.title()
df['Type'] = df['Type'].str.strip().str.title()

# -------------------------------
# FEATURE ENGINEERING
# -------------------------------
df['Month'] = df['Date'].dt.month_name()
df['Month_Num'] = df['Date'].dt.month
df['Weekday'] = df['Date'].dt.day_name()

# Save cleaned data
df.to_csv("data/cleaned_expenses.csv", index=False)

print("\n✅ Cleaned Data Saved")

# -------------------------------
# ANALYSIS
# -------------------------------
expense_df = df[df['Type'] == 'Expense']

category_spend = expense_df.groupby('Category')['Amount'].sum()
monthly_spend = expense_df.groupby('Month_Num')['Amount'].sum()

print("\n📊 Category Spending:")
print(category_spend)

print("\n📈 Monthly Spending:")
print(monthly_spend)

# -------------------------------
# INSIGHTS
# -------------------------------
print("\n💡 Insights:")

top_category = category_spend.idxmax()
top_amount = category_spend.max()

print(f"👉 Highest spending category: {top_category} (₹{top_amount})")

if len(monthly_spend) > 1:
    trend = "increasing" if monthly_spend.iloc[-1] > monthly_spend.iloc[0] else "decreasing"
    print(f"👉 Spending trend is {trend}")