import org.apache.spark.{SparkConf, SparkContext}

object ExpenseRDDAnalysis {
  def main(args: Array[String]): Unit = {
    val projectDir = new java.io.File("..").getCanonicalPath
    val csvPath = new java.io.File(projectDir, "data/expenses.csv").getPath

    val conf = new SparkConf()
      .setAppName("ExpenseRDDAnalysis")
      .setMaster("local[*]")

    val sc = new SparkContext(conf)
    sc.setLogLevel("ERROR")

    try {
      val lines = sc.textFile(csvPath)

      val expenses = lines
        .filter(line => !line.startsWith("transaction_id"))
        .flatMap { line =>
          val fields = line.split(",", -1)
          if (fields.length >= 5) {
            try {
              Some((fields(2).trim, fields(3).trim.toDouble))
            } catch {
              case _: NumberFormatException => None
            }
          } else {
            None
          }
        }

      println("\n=== Scala Spark RDD: Category-wise Expenses ===")

      expenses
        .map { case (category, amount) => (category, (amount, 1)) }
        .reduceByKey { case ((sum1, count1), (sum2, count2)) =>
          (sum1 + sum2, count1 + count2)
        }
        .collect()
        .sortBy(_._1)
        .foreach { case (category, (total, count)) =>
          println(f"$category%-18s Total: Rs. $total%.2f  Transactions: $count%d")
        }

      val total = expenses.map(_._2).sum()
      val count = expenses.count()

      println(f"\nOverall total: Rs. $total%.2f")
      println(s"Total transactions: $count")
    } finally {
      sc.stop()
    }
  }
}
