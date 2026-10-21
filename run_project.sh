#!/bin/bash

cd "$(dirname "$0")"

export JAVA_HOME="/opt/homebrew/opt/openjdk@11"
export PATH="$JAVA_HOME/bin:$PATH"

echo "=================================="
echo " Smart Expense Analytics System"
echo " Powered by Apache Spark"
echo "=================================="

python3 -m streamlit run dashboard/app.py
