# Smart Expense Analytics and Spending Prediction System

An expense analytics project built using Python, Apache Spark, PySpark, Streamlit, Pandas, Plotly, and Scikit-learn.

## Features

- Add expenses manually through the dashboard.
- Store transactions in a CSV file.
- Calculate total expenses and transaction counts using Apache Spark.
- Perform RDD-based expense filtering and category analysis.
- Run Spark SQL queries for category and payment-method analysis.
- Visualize expenses through a Streamlit dashboard.
- Demonstrate file-based PySpark Structured Streaming.
- Demonstrate monthly expense prediction using Linear Regression.

## Project Structure

- dashboard/app.py: Streamlit dashboard
- data/expenses.csv: Expense dataset
- data/stream_input/: Streaming input files
- outputs/expense_prediction.json: Prediction results
- src/rdd_analysis.py: RDD analysis
- src/spark_analytics.py: Spark analytics
- src/spark_sql_analysis.py: Spark SQL analysis
- src/expense_prediction.py: Prediction model
- src/streaming_analysis.py: File-based streaming
- requirements.txt: Python dependencies
- run_project.sh: Dashboard launcher

## Prerequisites

- Python 3
- Java 11
- Packages listed in requirements.txt

## Installation

Install dependencies using:

python3 -m pip install -r requirements.txt

Configure Java 11 on this Mac:

export JAVA_HOME=/opt/homebrew/opt/openjdk@11
export PATH="$JAVA_HOME/bin:$PATH"

## Run the Dashboard

./run_project.sh

Open the local URL shown in the terminal.

## Run Individual Modules

python3 src/rdd_analysis.py
python3 src/spark_sql_analysis.py
python3 src/expense_prediction.py
python3 src/streaming_analysis.py

For streaming, add new CSV files to data/stream_input/ while the streaming script is running.

## Important Notes

- Spark currently runs in local mode.
- Streaming uses file-based micro-batch processing, not Kafka.
- The current prediction model uses synthetic demonstration data, not actual expense history.
- Expenses are stored in a local CSV file. Authentication and persistent multi-user storage are not implemented yet.
