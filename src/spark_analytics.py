from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, count

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_DIR / "data" / "expenses.csv"

def analyze_expenses(csv_path=DATA_FILE):
    spark = (
        SparkSession.builder
        .appName("SmartExpenseAnalytics")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    try:
        df = spark.read.csv(
            str(csv_path),
            header=True,
            inferSchema=True
        )

        result = df.agg(
            sum("amount").alias("total_expenses"),
            count("*").alias("transaction_count")
        ).first()

        categories = (
            df.groupBy("category")
            .agg(
                sum("amount").alias("total_spent"),
                count("*").alias("transactions")
            )
            .orderBy("total_spent", ascending=False)
        )

        return result.asDict(), categories.toPandas()

    finally:
        spark.stop()
