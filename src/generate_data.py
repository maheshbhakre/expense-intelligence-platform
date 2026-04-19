import pandas as pd
import numpy as np

np.random.seed(42)

categories = ["Food", "Transport", "Bills", "Entertainment", "Rent", "Salary"]
payment_methods = ["UPI", "Card", "Cash", "Bank"]

data = []

for i in range(300):
    date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=np.random.randint(0, 120))
    category = np.random.choice(categories)

    if category == "Salary":
        amount = np.random.randint(30000, 60000)
        ttype = "Income"
    else:
        amount = np.random.randint(100, 5000)
        ttype = "Expense"

    payment = np.random.choice(payment_methods)

    data.append([date, category, "Auto Entry", amount, ttype, payment])

df = pd.DataFrame(data, columns=["Date","Category","Description","Amount","Type","Payment_Method"])
df.to_csv("data/expenses.csv", index=False)

print("✅ Synthetic dataset created (300 rows)")