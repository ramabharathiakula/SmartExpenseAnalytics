from pathlib import Path
from pyspark.sql import SparkSession

project_dir = Path(__file__).resolve().parent.parent
file_path = str(project_dir / "data" / "expenses.csv")

spark = (
    SparkSession.builder
    .appName("ExpenseRDDAnalysis")
    .master("local[2]")
    .getOrCreate()
)

sc = spark.sparkContext
sc.setLogLevel("ERROR")

try:
    lines = sc.textFile(file_path)
    header = lines.first()
    data = lines.filter(lambda line: line != header)

    expenses = data.map(
        lambda line: (
            line.split(",")[2],
            float(line.split(",")[3])
        )
    ).cache()

    print("\n--- Transactions Above ₹500 ---", flush=True)
    for category, amount in expenses.filter(
        lambda item: item[1] > 500
    ).collect():
        print(f"{category}: ₹{amount:.2f}", flush=True)

    print("\n--- Category-wise Spending ---", flush=True)
    for category, total in sorted(
        expenses.reduceByKey(lambda a, b: a + b).collect()
    ):
        print(f"{category}: ₹{total:.2f}", flush=True)

    print(f"\nTotal transactions: {data.count()}", flush=True)

finally:
    spark.stop()
