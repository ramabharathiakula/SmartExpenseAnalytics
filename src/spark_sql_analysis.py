from pathlib import Path
from pyspark.sql import SparkSession

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "expenses.csv"

spark = (
    SparkSession.builder
    .appName("ExpenseSparkSQL")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    df = spark.read.csv(
        str(DATA_FILE),
        header=True,
        inferSchema=True
    )

    df.createOrReplaceTempView("expenses")

    queries = {
        "Total Expenses": """
            SELECT SUM(amount) AS total_expenses
            FROM expenses
        """,
        "Category-wise Spending": """
            SELECT category, SUM(amount) AS total_spent,
                   COUNT(*) AS transactions
            FROM expenses
            GROUP BY category
            ORDER BY total_spent DESC
        """,
        "Transactions Above 500": """
            SELECT transaction_id, category, amount
            FROM expenses
            WHERE amount > 500
            ORDER BY amount DESC
        """,
        "Payment Method Analysis": """
            SELECT payment_method, SUM(amount) AS total_spent,
                   COUNT(*) AS transactions
            FROM expenses
            GROUP BY payment_method
            ORDER BY total_spent DESC
        """
    }

    for title, query in queries.items():
        print(f"\n--- {title} ---")
        spark.sql(query).show(truncate=False)

finally:
    spark.stop()
