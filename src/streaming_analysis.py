
from pathlib import Path
import signal
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, count

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "data" / "stream_input"
CHECKPOINT_DIR = PROJECT_DIR / "outputs" / "stream_checkpoint"

INPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

spark = (
    SparkSession.builder
    .appName("ExpenseStructuredStreaming")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

# Avoid PySpark's default Ctrl+C signal handler conflict.
signal.signal(signal.SIGINT, signal.SIG_IGN)

schema = """
transaction_id INT,
date DATE,
category STRING,
amount DOUBLE,
payment_method STRING
"""

stream_df = (
    spark.readStream
    .schema(schema)
    .option("header", True)
    .option("maxFilesPerTrigger", 1)
    .csv(str(INPUT_DIR))
)

summary = (
    stream_df.groupBy("category")
    .agg(
        sum("amount").alias("total_spent"),
        count("*").alias("transaction_count")
    )
)

query = (
    summary.writeStream
    .outputMode("complete")
    .format("console")
    .option("truncate", False)
    .option("checkpointLocation", str(CHECKPOINT_DIR))
    .start()
)

print("Expense streaming started.")
print(f"Add new CSV files to: {INPUT_DIR}")
print("Press Ctrl+C to stop.")

try:
    query.awaitTermination()
finally:
    print("\nStopping expense streaming...")
    try:
        query.stop()
    except Exception as e:
        print(f"Streaming shutdown notice: {e}")
    try:
        spark.stop()
    except Exception as e:
        print(f"Spark shutdown notice: {e}")
    print("Expense streaming stopped.")
