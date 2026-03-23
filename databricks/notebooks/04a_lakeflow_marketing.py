# Databricks notebook source
# MAGIC %md
# MAGIC # Lakeflow — Marketing Team Consumer Pipeline
# MAGIC
# MAGIC This is what the **marketing team** would need to build and maintain in Lakeflow
# MAGIC to get their own governed dataset on top of the platform gold tables.
# MAGIC
# MAGIC In **dbt Mesh**, the marketing team has a separate dbt Cloud project (`marketing/`)
# MAGIC with two models that use compile-time-validated cross-project refs:
# MAGIC ```sql
# MAGIC select * from {{ ref('platform', 'dim_customers') }}  -- validated, access: public enforced
# MAGIC select * from {{ ref('platform', 'fct_orders') }}     -- validated, contract enforced
# MAGIC ```
# MAGIC
# MAGIC In Lakeflow, this team needs **their own pipeline** reading from the platform output
# MAGIC via hardcoded table strings — no validation, no contract enforcement, no inherited metadata.
# MAGIC
# MAGIC **Run `01_lakeflow_pipeline.py` first** — this notebook reads from its gold tables.
# MAGIC
# MAGIC ## Pipeline configuration:
# MAGIC 1. **Jobs & Pipelines** → **Create** → **ETL pipeline**
# MAGIC 2. In the dialog: name = `ecommerce-lakeflow-marketing`, catalog = `enablement`, schema = `ecommerce_lakeflow_marketing` → **Create**
# MAGIC 3. On the "Next step" screen → **Add existing assets** → select this notebook → **Add**
# MAGIC 4. Click **Start** — creates 2 tables: `marketing_customer_segments`, `marketing_country_performance`

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, round as _round,
    when, coalesce, lit, datediff, current_date,
    max as _max
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reading from the platform gold layer
# MAGIC
# MAGIC In dbt Mesh, these two lines are compile-time validated:
# MAGIC ```sql
# MAGIC select * from {{ ref('platform', 'dim_customers') }}
# MAGIC select * from {{ ref('platform', 'fct_orders') }}
# MAGIC ```
# MAGIC If `dim_customers` is renamed or a column is removed, the dbt Cloud job fails
# MAGIC **before any SQL runs**. Below, these are hardcoded strings — failure happens
# MAGIC at runtime, silently, after data has already been processed.

# COMMAND ----------

@dlt.table(
    name="marketing_customer_segments",
    comment="""
        Customer segments for the marketing team.
        Segments: champion, loyal, at_risk, lapsed, never_purchased, other.

        NOTE: Segment thresholds (high_value >= $500, mid_value >= $100) are duplicated
        from 01_lakeflow_pipeline.py -> gold_dim_customers. If the platform team changes
        the definition, this table silently diverges until manually updated.

        dbt Mesh equivalent: marketing.mart_customer_segments (8 lines, validated ref)
        Lakeflow reads from: enablement.ecommerce_lakeflow.gold_dim_customers (hardcoded)
    """,
    table_properties={"quality": "gold", "team": "marketing"}
)
def marketing_customer_segments():
    # Hardcoded string — no compile-time validation, no access control.
    # dbt Mesh equivalent: {{ ref('platform', 'dim_customers') }}
    customers = spark.read.table("enablement.ecommerce_lakeflow.gold_dim_customers")
    orders    = spark.read.table("enablement.ecommerce_lakeflow.gold_fct_orders")

    recency = (
        orders
        .groupBy("customer_id")
        .agg(_max("order_date").alias("last_order_date"))
    )

    enriched = customers.join(recency, "customer_id", "left")

    # DUPLICATION ALERT: >= 500 / >= 100 thresholds are also in gold_dim_customers.
    # No mechanism exists to share or enforce this definition across pipelines.
    return (
        enriched
        .withColumn(
            "days_since_last_order",
            when(col("last_order_date").isNotNull(),
                 datediff(current_date(), col("last_order_date")))
            .otherwise(lit(9999))
        )
        .withColumn(
            "marketing_segment",
            when(
                (col("total_lifetime_value") >= 500) & (col("days_since_last_order") <= 30),
                "champion"
            )
            .when(col("number_of_orders") >= 3, "loyal")
            .when(
                (col("total_lifetime_value") >= 100) & (col("days_since_last_order") > 60),
                "at_risk"
            )
            .when(col("days_since_last_order") > 90, "lapsed")
            .when(col("number_of_orders") == 0, "never_purchased")
            .otherwise("other")
        )
        .select(
            "customer_id", "first_name", "last_name", "email", "country",
            "customer_segment", "total_lifetime_value", "number_of_orders",
            "last_order_date", "days_since_last_order", "marketing_segment"
        )
    )

# COMMAND ----------

@dlt.table(
    name="marketing_country_performance",
    comment="""
        Revenue and customer metrics by country for the marketing team.

        NOTE: The 'completed orders only' revenue filter is also defined in
        gold_fct_revenue in the platform pipeline. Two independent definitions —
        if the platform team changes revenue recognition, this must be updated separately.

        dbt Mesh equivalent: marketing.mart_country_performance (validated ref)
        Lakeflow reads from: enablement.ecommerce_lakeflow.gold_fct_orders (hardcoded)
    """,
    table_properties={"quality": "gold", "team": "marketing"}
)
def marketing_country_performance():
    # DUPLICATION: revenue recognition rule (status = 'completed') also in gold_fct_revenue
    orders    = spark.read.table("enablement.ecommerce_lakeflow.gold_fct_orders")
    customers = spark.read.table("enablement.ecommerce_lakeflow.gold_dim_customers")

    completed = orders.filter(col("status") == "completed")

    return (
        completed
        .join(customers.select("customer_id", "country"), "customer_id")
        .groupBy("country")
        .agg(
            count("order_id").alias("total_orders"),
            _round(_sum("amount_paid"), 2).alias("total_revenue"),
            _round(avg("amount_paid"), 2).alias("avg_order_value"),
            count("customer_id").alias("active_customers")
        )
        .withColumn(
            "revenue_per_customer",
            _round(col("total_revenue") / col("active_customers"), 2)
        )
        .orderBy(col("total_revenue").desc())
    )
