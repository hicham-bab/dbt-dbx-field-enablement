# Databricks notebook source
# MAGIC %md
# MAGIC # Lakeflow — Finance Team Consumer Pipeline
# MAGIC
# MAGIC This is what the **finance team** would need to build and maintain in Lakeflow
# MAGIC to get their own governed dataset on top of the platform gold tables.
# MAGIC
# MAGIC In **dbt Mesh**, the finance team has a separate dbt Cloud project (`finance/`)
# MAGIC with two models:
# MAGIC ```sql
# MAGIC -- fct_revenue.sql (8 lines total)
# MAGIC select * from {{ ref('platform', 'fct_orders') }}   -- validated, contract enforced
# MAGIC
# MAGIC -- fct_revenue_by_product.sql
# MAGIC select * from {{ ref('platform', 'fct_orders') }}   -- validated
# MAGIC -- Note: cannot ref staging models — access: protected blocks it at compile time
# MAGIC ```
# MAGIC
# MAGIC In Lakeflow, this team needs **their own pipeline** with hardcoded table strings,
# MAGIC duplicated business logic, and no protection against breaking changes upstream.
# MAGIC
# MAGIC **Run `01_lakeflow_pipeline.py` first** — this notebook reads from its gold tables.
# MAGIC
# MAGIC ## Pipeline configuration:
# MAGIC 1. **Jobs & Pipelines** → **Create** → **ETL pipeline**
# MAGIC 2. In the dialog: name = `ecommerce-lakeflow-finance`, catalog = `enablement`, schema = `ecommerce_lakeflow_finance` → **Create**
# MAGIC 3. On the "Next step" screen → **Add existing assets** → select this notebook → **Add**
# MAGIC 4. Click **Start** — creates 2 tables: `finance_fct_revenue`, `finance_fct_revenue_by_product`

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, round as _round,
    when, coalesce, lit
)

# Source catalog/schema for upstream gold tables — set via DLT pipeline configuration.
SOURCE_CATALOG = spark.conf.get("source_catalog", "enablement")
SOURCE_LF_SCHEMA = spark.conf.get("source_lakeflow_schema", "ecommerce_lakeflow")

# COMMAND ----------

# MAGIC %md
# MAGIC ## The dbt Mesh comparison
# MAGIC
# MAGIC `finance/models/fct_revenue.sql` in dbt Mesh is **8 lines**:
# MAGIC ```sql
# MAGIC select order_id, order_date, customer_id, status, amount_paid,
# MAGIC        case when status = 'completed' then amount_paid else 0 end as recognised_revenue,
# MAGIC        date_trunc('month', order_date) as revenue_month
# MAGIC from {{ ref('platform', 'fct_orders') }}
# MAGIC ```
# MAGIC One validated ref. Contract enforced. If `fct_orders` changes schema, the
# MAGIC dbt Cloud job fails before any consumer is affected.
# MAGIC
# MAGIC The Lakeflow equivalent below is longer, contains a copy of the business rule,
# MAGIC and will fail silently at runtime if the upstream schema changes.

# COMMAND ----------

@dlt.table(
    name="finance_fct_revenue",
    comment="""
        Revenue fact table for the finance team.
        recognised_revenue = amount_paid for completed orders, 0 otherwise.

        NOTE: Revenue recognition rule (status = 'completed') is duplicated from
        the platform pipeline's gold_fct_revenue. If the platform team adds a new
        status or changes revenue recognition logic, finance must update this
        pipeline separately — there is no contract linking them.

        dbt Mesh equivalent: finance.fct_revenue (8 lines, validated ref)
        Lakeflow reads from: enablement.ecommerce_lakeflow.gold_fct_orders (hardcoded)
    """,
    table_properties={"quality": "gold", "team": "finance"}
)
def finance_fct_revenue():
    # Hardcoded string — no compile-time validation, no contract.
    # dbt Mesh equivalent: {{ ref('platform', 'fct_orders') }}
    orders = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")

    return (
        orders
        .select(
            col("order_id"),
            col("order_date"),
            col("customer_id"),
            col("status"),
            col("amount_paid"),
            # DUPLICATION: this rule also lives in gold_fct_revenue in the platform pipeline.
            when(col("status") == "completed", col("amount_paid"))
            .otherwise(lit(0.0))
            .alias("recognised_revenue"),
            _round(
                col("amount_paid") - coalesce(col("items_total"), lit(0.0)), 2
            ).alias("payment_vs_items_delta")
        )
    )

# COMMAND ----------

@dlt.table(
    name="finance_fct_revenue_by_product",
    comment="""
        Revenue by product category for the finance team.

        NOTE: No product-level gold table exists in the platform pipeline, so finance
        reads directly from silver_products. In dbt Mesh, silver/staging models are
        access: protected — the finance project cannot compile a ref to them.
        In Lakeflow there is no such enforcement: any team can read any table at any layer.

        dbt Mesh equivalent: finance.fct_revenue_by_product (validated refs only to public models)
        Lakeflow reads from: enablement.ecommerce_lakeflow.gold_fct_orders (hardcoded)
                             enablement.ecommerce_lakeflow.silver_products  (hardcoded — bypassing gold layer)
    """,
    table_properties={"quality": "gold", "team": "finance"}
)
def finance_fct_revenue_by_product():
    orders = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")
    # Bypassing gold layer — reading silver directly because no product gold table exists.
    # In dbt Mesh this is impossible: staging is access: protected.
    products = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.silver_products")

    completed = orders.filter(col("status") == "completed")

    return (
        completed
        .crossJoin(products.select("product_id", "product_name", "category", "unit_price"))
        .groupBy("category", "product_name")
        .agg(
            count("order_id").alias("total_orders"),
            _round(_sum("amount_paid"), 2).alias("total_revenue"),
            _round(avg("amount_paid"), 2).alias("avg_order_value")
        )
        .orderBy(col("total_revenue").desc())
    )
