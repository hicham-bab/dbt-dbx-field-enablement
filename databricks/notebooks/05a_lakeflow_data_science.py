# Databricks notebook source
# MAGIC %md
# MAGIC # Lakeflow — Data Science Team Consumer Pipeline
# MAGIC
# MAGIC This is what the **DS team** would need to build and maintain in Lakeflow
# MAGIC to produce the same RFM features and churn features that the dbt `data_science`
# MAGIC project produces with 2 Python models and a cross-project ref.
# MAGIC
# MAGIC ## The duplication problem
# MAGIC
# MAGIC In **dbt Mesh**, the DS team writes:
# MAGIC ```python
# MAGIC customers = dbt.ref("platform", "dim_customers")  # validated, contracted
# MAGIC orders = dbt.ref("platform", "fct_orders")        # validated, contracted
# MAGIC ```
# MAGIC
# MAGIC In Lakeflow, the DS team writes:
# MAGIC ```python
# MAGIC customers = spark.read.table("enablement.ecommerce_lakeflow.gold_dim_customers")
# MAGIC orders = spark.read.table("enablement.ecommerce_lakeflow.gold_fct_orders")
# MAGIC ```
# MAGIC
# MAGIC Same data, but:
# MAGIC - **No contract enforcement.** If platform renames `total_lifetime_value` to `ltv`,
# MAGIC   the Lakeflow pipeline fails at runtime, after processing has started.
# MAGIC   dbt Mesh fails at compile time, before anything runs.
# MAGIC - **No single source of truth.** The "completed orders only" revenue filter,
# MAGIC   the "$500 high-value" threshold — all duplicated here. When platform changes
# MAGIC   these thresholds, DS models silently drift. Wrong predictions ship to production.
# MAGIC - **No lineage.** dbt Cloud Explorer shows DS depends on platform → you see the
# MAGIC   full DAG. In Lakeflow, the DS pipeline is a separate, disconnected pipeline.
# MAGIC
# MAGIC ## Pipeline configuration:
# MAGIC 1. **Jobs & Pipelines** → **Create** → **ETL pipeline**
# MAGIC 2. Name = `ecommerce-lakeflow-data-science`, catalog = `enablement`, schema = `ecommerce_lakeflow_ds`
# MAGIC 3. **Add existing assets** → select this notebook → **Add** → **Start**

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

# MAGIC %md
# MAGIC ## RFM Customer Features
# MAGIC
# MAGIC dbt Mesh equivalent: `data_science.rfm_customer_features` (1 Python model, ~80 lines)
# MAGIC
# MAGIC Below: the same logic, but with hardcoded table references, duplicated thresholds,
# MAGIC and no contract enforcement. If the platform team changes the customer segmentation
# MAGIC from $500/$100 to $600/$200, the RFM model here silently uses stale segments.

# COMMAND ----------

@dlt.table(
    name="ds_rfm_customer_features",
    comment="""
        RFM feature engineering for the DS team.

        DUPLICATION ALERT: This table reads from gold_dim_customers and gold_fct_orders
        via hardcoded strings. The segment thresholds (high_value >= $500) are defined
        in 01_lakeflow_pipeline.py. If platform changes them, this table silently drifts.

        dbt Mesh equivalent: data_science.rfm_customer_features (validated cross-project ref)
    """,
    table_properties={"quality": "gold", "team": "data_science"}
)
def ds_rfm_customer_features():
    # Hardcoded — no compile-time validation, no contract enforcement
    # dbt Mesh equivalent: dbt.ref("platform", "dim_customers")
    customers = spark.read.table("enablement.ecommerce_lakeflow.gold_dim_customers")
    orders = spark.read.table("enablement.ecommerce_lakeflow.gold_fct_orders")

    # Recency
    recency = (
        orders
        .groupBy("customer_id")
        .agg(
            F.max("order_date").alias("last_order_date"),
            F.min("order_date").alias("first_order_date"),
        )
        .withColumn("recency_days", F.datediff(F.current_date(), F.col("last_order_date")))
    )

    # Frequency — DUPLICATION: "completed" filter also in gold_fct_revenue
    frequency = (
        orders
        .filter(F.col("status") == "completed")
        .groupBy("customer_id")
        .agg(
            F.countDistinct("order_id").alias("frequency"),
            F.avg("amount_paid").alias("avg_order_value"),
        )
    )

    # Monetary — DUPLICATION: same "completed" filter
    monetary = (
        orders
        .filter(F.col("status") == "completed")
        .groupBy("customer_id")
        .agg(
            F.sum("amount_paid").alias("monetary_value"),
            F.sum("number_of_items").alias("total_items_purchased"),
        )
    )

    rfm = (
        customers
        .select("customer_id", "customer_segment", "country")
        .join(recency, "customer_id", "left")
        .join(frequency, "customer_id", "left")
        .join(monetary, "customer_id", "left")
        .fillna(0, subset=["recency_days", "frequency", "monetary_value",
                           "avg_order_value", "total_items_purchased"])
    )

    # Quintile scoring — same as dbt Python model
    recency_q = rfm.approxQuantile("recency_days", [0.2, 0.4, 0.6, 0.8], 0.05)
    frequency_q = rfm.approxQuantile("frequency", [0.2, 0.4, 0.6, 0.8], 0.05)
    monetary_q = rfm.approxQuantile("monetary_value", [0.2, 0.4, 0.6, 0.8], 0.05)

    rfm = rfm.withColumn(
        "r_score",
        F.when(F.col("recency_days") <= recency_q[0], 5)
        .when(F.col("recency_days") <= recency_q[1], 4)
        .when(F.col("recency_days") <= recency_q[2], 3)
        .when(F.col("recency_days") <= recency_q[3], 2)
        .otherwise(1)
    )
    rfm = rfm.withColumn(
        "f_score",
        F.when(F.col("frequency") <= frequency_q[0], 1)
        .when(F.col("frequency") <= frequency_q[1], 2)
        .when(F.col("frequency") <= frequency_q[2], 3)
        .when(F.col("frequency") <= frequency_q[3], 4)
        .otherwise(5)
    )
    rfm = rfm.withColumn(
        "m_score",
        F.when(F.col("monetary_value") <= monetary_q[0], 1)
        .when(F.col("monetary_value") <= monetary_q[1], 2)
        .when(F.col("monetary_value") <= monetary_q[2], 3)
        .when(F.col("monetary_value") <= monetary_q[3], 4)
        .otherwise(5)
    )
    rfm = rfm.withColumn("rfm_score", F.col("r_score") + F.col("f_score") + F.col("m_score"))

    return rfm.select(
        "customer_id", "customer_segment", "country",
        "recency_days", "frequency", "monetary_value",
        "avg_order_value", "total_items_purchased",
        "r_score", "f_score", "m_score", "rfm_score",
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Churn Feature Engineering
# MAGIC
# MAGIC dbt Mesh equivalent: `data_science.customer_churn_features` (1 Python model, ~90 lines)
# MAGIC
# MAGIC Same problem: every filter, threshold, and definition is duplicated.
# MAGIC The 90-day churn threshold here is independent of any other pipeline.
# MAGIC If the business redefines "churned" as 60 days, someone has to find
# MAGIC and update every notebook that uses 90. In dbt, it's one YAML change.

# COMMAND ----------

@dlt.table(
    name="ds_customer_churn_features",
    comment="""
        Customer churn feature vector for ML models.

        DUPLICATION ALERT: The 90-day churn threshold, the 'completed' order filter,
        and the return_rate calculation are all duplicated from other pipelines.
        No mechanism to enforce consistency across teams.

        dbt Mesh equivalent: data_science.customer_churn_features (validated ref)
    """,
    table_properties={"quality": "gold", "team": "data_science"}
)
def ds_customer_churn_features():
    customers = spark.read.table("enablement.ecommerce_lakeflow.gold_dim_customers")
    orders = spark.read.table("enablement.ecommerce_lakeflow.gold_fct_orders")

    order_window = Window.partitionBy("customer_id").orderBy("order_date")

    order_features = (
        orders
        .groupBy("customer_id")
        .agg(
            F.count("order_id").alias("total_orders"),
            F.countDistinct(F.when(F.col("status") == "completed", F.col("order_id"))).alias("completed_orders"),
            F.countDistinct(F.when(F.col("status") == "returned", F.col("order_id"))).alias("returned_orders"),
            F.sum("amount_paid").alias("total_spend"),
            F.avg("amount_paid").alias("avg_order_value"),
            F.stddev("amount_paid").alias("stddev_order_value"),
            F.avg("number_of_items").alias("avg_items_per_order"),
            F.max("order_date").alias("last_order_date"),
            F.min("order_date").alias("first_order_date"),
            F.countDistinct("payment_method").alias("distinct_payment_methods"),
        )
    )

    order_gaps = (
        orders
        .withColumn("prev_order_date", F.lag("order_date").over(order_window))
        .withColumn("days_between_orders", F.datediff(F.col("order_date"), F.col("prev_order_date")))
        .filter(F.col("days_between_orders").isNotNull())
        .groupBy("customer_id")
        .agg(
            F.avg("days_between_orders").alias("avg_days_between_orders"),
            F.stddev("days_between_orders").alias("stddev_days_between_orders"),
            F.max("days_between_orders").alias("max_gap_days"),
        )
    )

    features = (
        customers
        .select("customer_id", "customer_segment", "country",
                "total_lifetime_value", "number_of_orders",
                "first_order_date", "most_recent_order_date")
        .join(order_features, "customer_id", "left")
        .join(order_gaps, "customer_id", "left")
        .withColumn("days_since_last_order", F.datediff(F.current_date(), F.col("last_order_date")))
        .withColumn("customer_tenure_days", F.datediff(F.col("last_order_date"), F.col("first_order_date")))
        .withColumn(
            "return_rate",
            F.when(F.col("total_orders") > 0, F.round(F.col("returned_orders") / F.col("total_orders"), 4))
            .otherwise(0)
        )
        # DUPLICATION: 90-day threshold — also in marketing_customer_segments (180 days for "at_risk")
        # No single definition. No enforcement. Just hope everyone uses the same number.
        .withColumn("is_churned", F.when(F.col("days_since_last_order") > 90, True).otherwise(False))
        .fillna(0, subset=[
            "total_orders", "completed_orders", "returned_orders",
            "total_spend", "avg_order_value", "stddev_order_value",
            "avg_items_per_order", "avg_days_between_orders",
            "stddev_days_between_orders", "max_gap_days",
            "distinct_payment_methods", "return_rate",
        ])
    )

    return features.select(
        "customer_id", "customer_segment", "country",
        "total_lifetime_value", "customer_tenure_days",
        "total_orders", "completed_orders", "returned_orders",
        "total_spend", "avg_order_value", "stddev_order_value",
        "avg_items_per_order", "days_since_last_order",
        "avg_days_between_orders", "stddev_days_between_orders",
        "max_gap_days", "distinct_payment_methods", "return_rate",
        "is_churned",
    )
