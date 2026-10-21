import json
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date
import sys
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.spark_analytics import analyze_expenses

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Smart Expense Analytics",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Smart Expense Analytics")
st.caption("Expense analysis powered by Apache Spark")

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------
project_dir = Path(__file__).resolve().parent.parent
default_file = project_dir / "data" / "expenses.csv"

default_file.parent.mkdir(parents=True, exist_ok=True)

required_columns = [
    "transaction_id",
    "date",
    "category",
    "amount",
    "payment_method"
]

# Create CSV if it does not exist
if not default_file.exists():
    pd.DataFrame(columns=required_columns).to_csv(
        default_file, index=False
    )

# --------------------------------------------------
# MANUAL EXPENSE ENTRY
# --------------------------------------------------
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input(
        "Expense Date",
        value=date.today()
    )

    category = st.selectbox(
        "Category",
        [
            "Food",
            "Transport",
            "Education",
            "Shopping",
            "Entertainment",
            "Other"
        ]
    )

    amount = st.number_input(
        "Amount (₹)",
        min_value=1.0,
        value=1.0,
        step=10.0
    )

    payment_method = st.selectbox(
        "Payment Method",
        ["UPI", "Cash", "Card", "Other"]
    )

    submitted = st.form_submit_button("Save Expense")

    if submitted:
        try:
            saved_df = pd.read_csv(default_file)

            if saved_df.empty:
                next_id = 1
            else:
                ids = pd.to_numeric(
                    saved_df["transaction_id"],
                    errors="coerce"
                )
                next_id = int(ids.max()) + 1 if ids.notna().any() else 1

            new_expense = pd.DataFrame([{
                "transaction_id": next_id,
                "date": expense_date.isoformat(),
                "category": category,
                "amount": amount,
                "payment_method": payment_method
            }])

            new_expense.to_csv(
                default_file,
                mode="a",
                header=False,
                index=False
            )

            st.sidebar.success("Expense saved successfully!")
            st.rerun()

        except Exception as error:
            st.sidebar.error(f"Could not save expense: {error}")

# --------------------------------------------------
# CSV UPLOAD
# --------------------------------------------------
st.sidebar.divider()
st.sidebar.subheader("📂 Upload Expense CSV")

uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)

# Saved CSV is the default source.
# Uploaded CSV is used for viewing and charts.
try:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.info("Dashboard is showing the uploaded CSV.")
    else:
        df = pd.read_csv(default_file)

except Exception as error:
    st.error(f"Could not read CSV: {error}")
    st.stop()

# --------------------------------------------------
# VALIDATE AND CLEAN DATA
# --------------------------------------------------
missing_columns = set(required_columns) - set(df.columns)

if missing_columns:
    st.error(
        "CSV is missing columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["category"] = df["category"].astype("string").str.strip()

df = df.dropna(
    subset=["date", "amount", "category", "payment_method"]
)

df = df[df["category"] != ""]

if df.empty:
    st.warning("No valid expenses found. Add an expense or upload a valid CSV.")
    st.stop()

# --------------------------------------------------
# APACHE SPARK ANALYTICS
# Spark processes the project's saved CSV.
# --------------------------------------------------
st.subheader("⚡ Apache Spark Processing Results")

try:
    spark_summary, spark_categories = analyze_expenses(default_file)

    spark_col1, spark_col2 = st.columns(2)

    spark_col1.metric(
        "Spark Total Expenses",
        f"₹{float(spark_summary['total_expenses'] or 0):,.2f}"
    )

    spark_col2.metric(
        "Spark Transaction Count",
        f"{int(spark_summary['transaction_count'] or 0)}"
    )

    st.write("Spark Category-wise Analysis")

    st.dataframe(
        spark_categories,
        use_container_width=True,
        hide_index=True
    )

except Exception as error:
    st.error(f"Spark processing error: {error}")

# --------------------------------------------------
# MONTHLY EXPENSE PREDICTION
# --------------------------------------------------
st.subheader("🔮 Monthly Expense Prediction")

prediction_file = project_dir / "outputs" / "expense_prediction.json"

try:
    if not prediction_file.exists():
        result = subprocess.run(
            [sys.executable, str(project_dir / "src" / "expense_prediction.py")],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)

    with open(prediction_file, "r") as file:
        prediction_data = json.load(file)

    data_type = prediction_data.get("data_type", "unknown")
    if data_type == "synthetic demonstration data":
        st.info(
            "Demo prediction: this estimate uses sample monthly data, "
            "not your actual expense history."
        )
    elif data_type == "actual expenses.csv data":
        st.info("Prediction analysis uses your recorded expenses.csv data.")

    historical_months = prediction_data.get("historical_months")
    if historical_months is not None:
        st.write(f"Historical months available: {historical_months}")

    status = prediction_data.get("prediction_status")

    if status == "insufficient_history":
        st.warning(
            prediction_data.get(
                "note",
                "More monthly expense history is needed before forecasting."
            )
        )
        monthly_totals = prediction_data.get("monthly_totals", [])
        if monthly_totals:
            st.write("Recorded monthly totals")
            st.dataframe(
                pd.DataFrame(monthly_totals),
                use_container_width=True,
                hide_index=True
            )

    elif status == "basic_forecast":
        predicted_expenses = prediction_data.get("predicted_expenses")
        predicted_month = prediction_data.get("predicted_month", "Next month")

        if predicted_expenses is not None:
            st.metric(
                f"Estimated Expenses — {predicted_month}",
                f"₹{float(predicted_expenses):,.2f}"
            )

        rmse = prediction_data.get("test_rmse")
        mae = prediction_data.get("test_mae")
        r2 = prediction_data.get("test_r2")

        metric_cols = st.columns(3)
        metric_cols[0].metric(
            "Test RMSE",
            f"₹{float(rmse):,.2f}" if rmse is not None else "N/A"
        )
        metric_cols[1].metric(
            "Test MAE",
            f"₹{float(mae):,.2f}" if mae is not None else "N/A"
        )
        metric_cols[2].metric(
            "Test R²",
            f"{float(r2):.4f}" if r2 is not None else "N/A"
        )
        st.caption(
            "This is a basic trend estimate. Forecast reliability depends "
            "on the amount and quality of historical data."
        )

    else:
        # Supports older prediction JSON files without a status field.
        predicted_expenses = prediction_data.get("predicted_expenses")
        rmse = prediction_data.get("test_rmse")

        if predicted_expenses is not None and rmse is not None:
            pred_col1, pred_col2 = st.columns(2)
            pred_col1.metric(
                "Estimated Next-Month Expenses",
                f"₹{float(predicted_expenses):,.2f}"
            )
            pred_col2.metric(
                "Prediction Test RMSE",
                f"₹{float(rmse):,.2f}"
            )
        else:
            st.warning(
                "Prediction is unavailable. More monthly expense history "
                "may be needed."
            )

except FileNotFoundError:
    st.warning(
        "Prediction file not found. Run src/expense_prediction.py first."
    )
except (ValueError, KeyError, TypeError) as error:
    st.error(f"Could not load prediction results: {error}")

# DASHBOARD SUMMARY
# --------------------------------------------------
total = df["amount"].sum()
average = df["amount"].mean()
transaction_count = len(df)

col1, col2, col3 = st.columns(3)

col1.metric("Total Expenses", f"₹{total:,.2f}")
col2.metric("Transactions", f"{transaction_count}")
col3.metric("Average Expense", f"₹{average:,.2f}")

# --------------------------------------------------
# CATEGORY-WISE BAR CHART
# --------------------------------------------------
category_totals = (
    df.groupby("category", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

st.subheader("📊 Spending by Category")

fig1 = px.bar(
    category_totals,
    x="category",
    y="amount",
    color="category",
    labels={
        "category": "Category",
        "amount": "Amount (₹)"
    },
    text_auto=".2s"
)

st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------
# EXPENSE DISTRIBUTION
# --------------------------------------------------
st.subheader("🍩 Expense Distribution")

fig2 = px.pie(
    category_totals,
    names="category",
    values="amount",
    hole=0.4
)

st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# DAILY SPENDING CHART
# --------------------------------------------------
st.subheader("📈 Spending Over Time")

daily = (
    df.assign(date=df["date"].dt.date)
    .groupby("date", as_index=False)["amount"]
    .sum()
    .sort_values("date")
)

fig3 = px.line(
    daily,
    x="date",
    y="amount",
    markers=True,
    labels={
        "date": "Date",
        "amount": "Amount (₹)"
    }
)

st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------
# TRANSACTION DETAILS
# --------------------------------------------------
st.subheader("🧾 Transaction Details")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# DOWNLOAD REPORT
# --------------------------------------------------
st.download_button(
    "⬇️ Download Expense Data",
    data=df.to_csv(index=False),
    file_name="expense_report.csv",
    mime="text/csv"
)
