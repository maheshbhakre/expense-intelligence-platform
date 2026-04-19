import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs("outputs/charts", exist_ok=True)

df = pd.read_csv("data/cleaned_expenses.csv")

sns.set(style="whitegrid")

expense_df = df[df['Type'] == 'Expense']

# Category chart
category = expense_df.groupby('Category')['Amount'].sum()

plt.figure()
category.plot(kind='bar')
plt.title("Category-wise Spending")
plt.ylabel("Amount")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("outputs/charts/category_spending.png")
plt.close()

# Pie chart
plt.figure()
category.plot(kind='pie', autopct='%1.1f%%')
plt.title("Expense Distribution")
plt.ylabel("")
plt.savefig("outputs/charts/pie_chart.png")
plt.close()

# Monthly trend
monthly = expense_df.groupby('Month_Num')['Amount'].sum()

plt.figure()
monthly.plot(marker='o')
plt.title("Monthly Expense Trend")
plt.xlabel("Month")
plt.ylabel("Amount")
plt.savefig("outputs/charts/monthly_trend.png")
plt.close()

print("✅ Charts saved")