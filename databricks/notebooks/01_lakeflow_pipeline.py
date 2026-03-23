# Databricks notebook source
# MAGIC %md
# MAGIC # Lakeflow (Delta Live Tables) — E-Commerce Pipeline
# MAGIC
# MAGIC ## What this shows dbt field teams:
# MAGIC - How Databricks solves the same medallion pattern problem natively
# MAGIC - DLT declarative syntax vs dbt SQL models
# MAGIC - What DLT has: auto-lineage, auto-retry, expectations (data quality)
# MAGIC - What DLT doesn't have: ref(), version-controlled docs, test suite, CI/CD environments
# MAGIC
# MAGIC ## Pipeline configuration:
# MAGIC 1. **Jobs & Pipelines** → **Create** → **ETL pipeline**
# MAGIC 2. In the dialog: name = `ecommerce-lakeflow-demo`, catalog = `enablement`, schema = `ecommerce_lakeflow` → **Create**
# MAGIC 3. On the "Next step" screen → **Add existing assets** → select this notebook
# MAGIC 4. Click **Start** — creates all 13 tables (5 bronze + 5 silver + 3 gold)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer — Raw Ingestion
# MAGIC
# MAGIC Bronze tables ingest raw data as-is from source tables. No transformations, no cleaning.
# MAGIC
# MAGIC **dbt equivalent:** `source()` declarations in `_sources.yml`

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, lower, upper, to_date,
    sum as _sum, count, avg,
    when, coalesce, lit,
    max as _max, min as _min,
    date_format, round as _round
)

# COMMAND ----------

@dlt.table(
    name="bronze_customers",
    comment="Raw customer data from source system",
    table_properties={"quality": "bronze"}
)
def bronze_customers():
    return spark.read.table("enablement.ecommerce.raw_customers")

# COMMAND ----------

@dlt.table(
    name="bronze_orders",
    comment="Raw orders from source system",
    table_properties={"quality": "bronze"}
)
def bronze_orders():
    return spark.read.table("enablement.ecommerce.raw_orders")

# COMMAND ----------

@dlt.table(
    name="bronze_order_items",
    comment="Raw order line items",
    table_properties={"quality": "bronze"}
)
def bronze_order_items():
    return spark.read.table("enablement.ecommerce.raw_order_items")

# COMMAND ----------

@dlt.table(
    name="bronze_products",
    comment="Raw product catalog",
    table_properties={"quality": "bronze"}
)
def bronze_products():
    return spark.read.table("enablement.ecommerce.raw_products")

# COMMAND ----------

@dlt.table(
    name="bronze_payments",
    comment="Raw payment transactions",
    table_properties={"quality": "bronze"}
)
def bronze_payments():
    return spark.read.table("enablement.ecommerce.raw_payments")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer — Cleaned and Standardized
# MAGIC
# MAGIC **dbt equivalent:** staging models. DLT Expectations are similar to dbt tests, **BUT**:
# MAGIC they live in Python code, not YAML. There is no auto-generated docs site. There are
# MAGIC only 3 expectation types (`expect`, `expect_or_drop`, `expect_or_fail`) vs dbt's
# MAGIC 4 built-in tests + unlimited custom SQL tests.

# COMMAND ----------

@dlt.table(
    name="silver_customers",
    comment="Cleaned and standardized customer records",
    table_properties={"quality": "silver"}
)
@dlt.expect("valid_email", "email IS NOT NULL")
@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
def silver_customers():
    return (
        dlt.read("bronze_customers")
        .select(
            col("customer_id"),
            col("first_name"),
            col("last_name"),
            lower(col("email")).alias("email"),
            to_date(col("created_at")).alias("created_date"),
            upper(col("country")).alias("country")
        )
    )

# COMMAND ----------

@dlt.table(
    name="silver_orders",
    comment="Cleaned orders with standardized status values",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
@dlt.expect("valid_status", "status IN ('placed', 'shipped', 'completed', 'returned')")
def silver_orders():
    return (
        dlt.read("bronze_orders")
        .select(
            col("order_id"),
            col("customer_id"),
            lower(col("status")).alias("status"),
            to_date(col("order_date")).alias("order_date"),
            col("amount")
        )
    )

# COMMAND ----------

@dlt.table(
    name="silver_order_items",
    comment="Cleaned order line items with validated quantities",
    table_properties={"quality": "silver"}
)
@dlt.expect("positive_quantity", "quantity > 0")
@dlt.expect_or_drop("valid_item", "order_item_id IS NOT NULL")
def silver_order_items():
    return (
        dlt.read("bronze_order_items")
        .select(
            col("order_item_id"),
            col("order_id"),
            col("product_id"),
            col("quantity"),
            col("unit_price"),
            (col("quantity") * col("unit_price")).alias("line_total")
        )
    )

# COMMAND ----------

@dlt.table(
    name="silver_products",
    comment="Cleaned product catalog",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_product_id", "product_id IS NOT NULL")
def silver_products():
    return (
        dlt.read("bronze_products")
        .select(
            col("product_id"),
            col("product_name"),
            lower(col("category")).alias("category"),
            col("unit_price"),
            col("is_active")
        )
    )

# COMMAND ----------

@dlt.table(
    name="silver_payments",
    comment="Cleaned payment records",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_payment_id", "payment_id IS NOT NULL")
@dlt.expect("positive_amount", "amount > 0")
def silver_payments():
    return (
        dlt.read("bronze_payments")
        .select(
            col("payment_id"),
            col("order_id"),
            lower(col("payment_method")).alias("payment_method"),
            col("amount"),
            to_date(col("payment_date")).alias("payment_date"),
            lower(col("status")).alias("payment_status")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer — Business Entities
# MAGIC
# MAGIC **dbt equivalent:** marts models. Key differences:
# MAGIC - In dbt, a business analyst can read the SQL directly
# MAGIC - In DLT, they need to understand PySpark
# MAGIC - dbt's `ref()` creates explicit, compile-time-validated lineage
# MAGIC - DLT infers lineage from `dlt.read()` calls at runtime

# COMMAND ----------

@dlt.table(
    name="gold_dim_customers",
    comment="Customer dimension with lifetime value metrics and segmentation",
    table_properties={"quality": "gold"}
)
def gold_dim_customers():
    customers = dlt.read("silver_customers")
    orders    = dlt.read("silver_orders")
    payments  = dlt.read("silver_payments")

    order_metrics = (
        orders
        .groupBy("customer_id")
        .agg(
            count("order_id").alias("number_of_orders"),
            _min("order_date").alias("first_order_date"),
            _max("order_date").alias("most_recent_order_date")
        )
    )

    payment_totals = (
        payments
        .join(orders.select("order_id", "customer_id"), "order_id")
        .filter(col("payment_status") == "success")
        .groupBy("customer_id")
        .agg(_round(_sum("amount"), 2).alias("total_lifetime_value"))
    )

    return (
        customers
        .join(order_metrics, "customer_id", "left")
        .join(payment_totals, "customer_id", "left")
        .select(
            col("customer_id"),
            col("first_name"),
            col("last_name"),
            col("email"),
            col("country"),
            col("created_date"),
            coalesce(col("number_of_orders"), lit(0)).alias("number_of_orders"),
            col("first_order_date"),
            col("most_recent_order_date"),
            coalesce(col("total_lifetime_value"), lit(0.0)).alias("total_lifetime_value"),
            when(col("total_lifetime_value") >= 500, "high_value")
            .when(col("total_lifetime_value") >= 100, "mid_value")
            .otherwise("low_value")
            .alias("customer_segment")
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_fct_orders",
    comment="Order fact table enriched with item counts and payment totals",
    table_properties={"quality": "gold"}
)
def gold_fct_orders():
    orders      = dlt.read("silver_orders")
    order_items = dlt.read("silver_order_items")
    payments    = dlt.read("silver_payments")

    item_metrics = (
        order_items
        .groupBy("order_id")
        .agg(
            count("order_item_id").alias("number_of_items"),
            _sum("line_total").alias("items_total")
        )
    )

    payment_metrics = (
        payments
        .filter(col("payment_status") == "success")
        .groupBy("order_id")
        .agg(_sum("amount").alias("amount_paid"))
    )

    return (
        orders
        .join(item_metrics,    "order_id", "left")
        .join(payment_metrics, "order_id", "left")
        .select(
            col("order_id"),
            col("customer_id"),
            col("status"),
            col("order_date"),
            col("amount"),
            coalesce(col("number_of_items"), lit(0)).alias("number_of_items"),
            coalesce(col("items_total"),     lit(0.0)).alias("items_total"),
            coalesce(col("amount_paid"),     lit(0.0)).alias("amount_paid")
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_fct_revenue",
    comment="Daily revenue aggregates for completed orders",
    table_properties={"quality": "gold"}
)
def gold_fct_revenue():
    fct_orders = dlt.read("gold_fct_orders")

    return (
        fct_orders
        .filter(col("status") == "completed")
        .groupBy("order_date")
        .agg(
            _sum("amount_paid").alias("daily_revenue"),
            count("order_id").alias("number_of_orders"),
            _round(avg("amount_paid"), 2).alias("avg_order_value")
        )
        .withColumn("revenue_month", date_format(col("order_date"), "yyyy-MM"))
        .orderBy("order_date")
    )
