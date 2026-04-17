"""
RFM (Recency, Frequency, Monetary) feature engineering for customer scoring.

This Python model runs on Databricks via PySpark.
It consumes the platform project's governed marts through dbt Mesh,
ensuring the DS team uses the same customer and order definitions
as marketing and finance — no duplication, single source of truth.

Lakeflow equivalent: see databricks/notebooks/05a_lakeflow_data_science.py
In Lakeflow, this logic is duplicated, thresholds drift, and there is no
contract enforcement when the platform team changes dim_customers.
"""


def model(dbt, session):
    from pyspark.sql import functions as F

    # Cross-project ref — validated at compile time by dbt Mesh.
    # If platform renames dim_customers, this build fails immediately.
    customers = dbt.ref("platform", "dim_customers")
    orders = dbt.ref("platform", "fct_orders")

    # ── Recency: days since last order ─────────────────────────────────────
    recency = (
        orders
        .groupBy("customer_id")
        .agg(
            F.max("order_date").alias("last_order_date"),
            F.min("order_date").alias("first_order_date"),
        )
        .withColumn(
            "recency_days",
            F.datediff(F.current_date(), F.col("last_order_date"))
        )
    )

    # ── Frequency: count of completed orders ───────────────────────────────
    frequency = (
        orders
        .filter(F.col("status") == "completed")
        .groupBy("customer_id")
        .agg(
            F.countDistinct("order_id").alias("frequency"),
            F.avg("amount_paid").alias("avg_order_value"),
        )
    )

    # ── Monetary: total spend (completed orders only) ──────────────────────
    monetary = (
        orders
        .filter(F.col("status") == "completed")
        .groupBy("customer_id")
        .agg(
            F.sum("amount_paid").alias("monetary_value"),
            F.sum("number_of_items").alias("total_items_purchased"),
        )
    )

    # ── Assemble RFM features ──────────────────────────────────────────────
    rfm = (
        customers
        .select("customer_id", "customer_segment", "country")
        .join(recency, "customer_id", "left")
        .join(frequency, "customer_id", "left")
        .join(monetary, "customer_id", "left")
        .fillna(0, subset=["recency_days", "frequency", "monetary_value",
                           "avg_order_value", "total_items_purchased"])
    )

    # ── Quintile scoring (1–5) using approxQuantile ────────────────────────
    recency_quantiles = rfm.approxQuantile("recency_days", [0.2, 0.4, 0.6, 0.8], 0.05)
    frequency_quantiles = rfm.approxQuantile("frequency", [0.2, 0.4, 0.6, 0.8], 0.05)
    monetary_quantiles = rfm.approxQuantile("monetary_value", [0.2, 0.4, 0.6, 0.8], 0.05)

    # Recency: lower is better → reverse scoring
    rfm = rfm.withColumn(
        "r_score",
        F.when(F.col("recency_days") <= recency_quantiles[0], 5)
        .when(F.col("recency_days") <= recency_quantiles[1], 4)
        .when(F.col("recency_days") <= recency_quantiles[2], 3)
        .when(F.col("recency_days") <= recency_quantiles[3], 2)
        .otherwise(1)
    )

    # Frequency: higher is better
    rfm = rfm.withColumn(
        "f_score",
        F.when(F.col("frequency") <= frequency_quantiles[0], 1)
        .when(F.col("frequency") <= frequency_quantiles[1], 2)
        .when(F.col("frequency") <= frequency_quantiles[2], 3)
        .when(F.col("frequency") <= frequency_quantiles[3], 4)
        .otherwise(5)
    )

    # Monetary: higher is better
    rfm = rfm.withColumn(
        "m_score",
        F.when(F.col("monetary_value") <= monetary_quantiles[0], 1)
        .when(F.col("monetary_value") <= monetary_quantiles[1], 2)
        .when(F.col("monetary_value") <= monetary_quantiles[2], 3)
        .when(F.col("monetary_value") <= monetary_quantiles[3], 4)
        .otherwise(5)
    )

    # Composite RFM score
    rfm = rfm.withColumn(
        "rfm_score",
        F.col("r_score") + F.col("f_score") + F.col("m_score")
    )

    return rfm.select(
        "customer_id", "customer_segment", "country",
        "recency_days", "frequency", "monetary_value",
        "avg_order_value", "total_items_purchased",
        "r_score", "f_score", "m_score", "rfm_score",
    )
