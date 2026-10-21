from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, count

spark = SparkSession.builder \
    .appName("SmartExpenseAnalytics") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

df = spark.read.csv("data/expenses.csv", header=True, inferSchema=True)

print("\n--- Expense Dataset ---")
df.show(5)

print("\n--- Total Expenses ---")
df.select(sum("amount").alias("total_expenses")).show()

print("\n--- Category-wise Expenses ---")
df.groupBy("category") \
    .agg(
        sum("amount").alias("total_spent"),
        count("*").alias("transactions")
    ) \
    .orderBy("total_spent", ascending=False) \
    .show()

spark.stop()
