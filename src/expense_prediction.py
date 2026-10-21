from pathlib import Path
import json
import calendar

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "expenses.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)
required = {"date", "amount"}
if not required.issubset(df.columns):
    raise ValueError("expenses.csv must contain date and amount columns.")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df.dropna(subset=["date", "amount"])

if df.empty:
    raise ValueError("No valid expense records found in expenses.csv.")

df["month"] = df["date"].dt.to_period("M")
monthly = (
    df.groupby("month", as_index=False)["amount"]
    .sum()
    .sort_values("month")
)
monthly["month_number"] = range(1, len(monthly) + 1)

print("\n--- Actual Expense History ---")
for _, row in monthly.iterrows():
    print(f"{row['month']}: ₹{row['amount']:.2f}")

results = {
    "data_type": "actual expenses.csv data",
    "historical_months": int(len(monthly)),
    "monthly_totals": [
        {
            "month": str(row["month"]),
            "total_expenses": round(float(row["amount"]), 2)
        }
        for _, row in monthly.iterrows()
    ],
    "prediction_status": "insufficient_history",
    "predicted_month": None,
    "predicted_expenses": None,
    "test_rmse": None,
    "test_mae": None,
    "test_r2": None,
    "note": (
        "At least 3 distinct months are required for a basic demonstration "
        "forecast. More historical months are recommended for a reliable estimate."
    )
}

# Use a basic time-trend model only when enough distinct months exist.
if len(monthly) >= 3:
    X = monthly[["month_number"]]
    y = monthly["amount"]

    # Evaluate on the latest month, training on all earlier months.
    train_X, test_X = X.iloc[:-1], X.iloc[-1:]
    train_y, test_y = y.iloc[:-1], y.iloc[-1:]

    evaluation_model = LinearRegression()
    evaluation_model.fit(train_X, train_y)
    test_prediction = evaluation_model.predict(test_X)

    results["test_rmse"] = round(
        float(np.sqrt(mean_squared_error(test_y, test_prediction))), 2
    )
    results["test_mae"] = round(
        float(mean_absolute_error(test_y, test_prediction)), 2
    )

    if len(monthly) >= 4:
        results["test_r2"] = round(
            float(r2_score(test_y, test_prediction)), 4
        )

    model = LinearRegression()
    model.fit(X, y)
    next_month_number = int(monthly["month_number"].max() + 1)
    prediction = max(0.0, float(model.predict(
        pd.DataFrame({"month_number": [next_month_number]})
    )[0]))

    last_period = monthly["month"].iloc[-1]
    next_period = last_period + 1

    results.update({
        "prediction_status": "basic_forecast",
        "predicted_month": str(next_period),
        "predicted_month_number": next_month_number,
        "predicted_expenses": round(prediction, 2),
        "note": (
            "Basic linear-trend estimate from actual recorded monthly totals. "
            "It is not a reliable financial forecast with only a few months of data."
        )
    })

output_file = OUTPUT_DIR / "expense_prediction.json"
output_file.write_text(json.dumps(results, indent=2))

print("\n--- Expense Prediction Results ---")
print(f"Data: {results['data_type']}")
print(f"Historical months: {results['historical_months']}")

if results["prediction_status"] == "basic_forecast":
    print(f"Predicted month: {results['predicted_month']}")
    print(f"Estimated expenses: ₹{results['predicted_expenses']:,.2f}")
    print(f"Test RMSE: ₹{results['test_rmse']:,.2f}")
    print(f"Test MAE: ₹{results['test_mae']:,.2f}")
    print(f"Test R²: {results['test_r2']}")
else:
    print("Prediction unavailable: not enough distinct monthly history.")
    print(results["note"])

print(f"\nResults saved to: {output_file}")
