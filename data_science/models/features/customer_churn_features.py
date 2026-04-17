"""
Churn prediction feature engineering.

Builds a feature vector per customer for downstream ML models.
Consumes platform marts via dbt Mesh — same governed definitions
that marketing and finance use.

Key point for the demo: in Databricks without Mesh, the DS team
would duplicate the "high_value >= $500" threshold, the "completed"
order filter, and the segmentation logic. When platform changes
any of these, DS models silently drift — no contract enforcement,
no build failure, just wrong predictions shipped to production.
"""


def model(dbt, session):
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window

    customers = dbt.ref("platform", "dim_customers")
    orders = dbt.ref("platform", "fct_orders")

    # ── Order-level behavioral features ────────────────────────────────────
    order_features = (
        orders
        .groupBy("customer_id")
        .agg(
            F.count("order_id").alias("total_orders"),
            F.countDistinct(
                F.when(F.col("status") == "completed", F.col("order_id"))
            ).alias("completed_orders"),
            F.countDistinct(
                F.when(F.col("status") == "returned", F.col("order_id"))
            ).alias("returned_orders"),
            F.sum("amount_paid").alias("total_spend"),
            F.avg("amount_paid").alias("avg_order_value"),
            F.stddev("amount_paid").alias("stddev_order_value"),
            F.avg("number_of_items").alias("avg_items_per_order"),
            F.max("order_date").alias("last_order_date"),
            F.min("order_date").alias("first_order_date"),
            F.countDistinct("payment_method").alias("distinct_payment_methods"),
        )
    )

    # ── Inter-order timing features ────────────────────────────────────────
    order_window = Window.partitionBy("customer_id").orderBy("order_date")

    order_gaps = (
        orders
        .withColumn("prev_order_date", F.lag("order_date").over(order_window))
        .withColumn(
            "days_between_orders",
            F.datediff(F.col("order_date"), F.col("prev_order_date"))
        )
        .filter(F.col("days_between_orders").isNotNull())
        .groupBy("customer_id")
        .agg(
            F.avg("days_between_orders").alias("avg_days_between_orders"),
            F.stddev("days_between_orders").alias("stddev_days_between_orders"),
            F.max("days_between_orders").alias("max_gap_days"),
        )
    )

    # ── Assemble feature vector ────────────────────────────────────────────
    features = (
        customers
        .select(
            "customer_id", "customer_segment", "country",
            "total_lifetime_value", "number_of_orders",
            "first_order_date", "most_recent_order_date",
        )
        .join(order_features, "customer_id", "left")
        .join(order_gaps, "customer_id", "left")
        .withColumn(
            "days_since_last_order",
            F.datediff(F.current_date(), F.col("last_order_date"))
        )
        .withColumn(
            "customer_tenure_days",
            F.datediff(F.col("last_order_date"), F.col("first_order_date"))
        )
        .withColumn(
            "return_rate",
            F.when(
                F.col("total_orders") > 0,
                F.round(F.col("returned_orders") / F.col("total_orders"), 4)
            ).otherwise(0)
        )
        .withColumn(
            "is_churned",
            F.when(F.col("days_since_last_order") > 90, True).otherwise(False)
        )
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
