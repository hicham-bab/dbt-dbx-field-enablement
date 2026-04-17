# Databricks notebook source
# MAGIC %md
# MAGIC # Lakeflow — Cross-Team Consumer Pipelines
# MAGIC # (The Mesh Equivalent You'd Have To Build Manually)
# MAGIC
# MAGIC ## What this notebook is for
# MAGIC
# MAGIC In **dbt Mesh**, the `marketing` and `finance` teams each have their own dbt Cloud project.
# MAGIC They consume platform models using `{{ ref('platform', 'fct_orders') }}` —
# MAGIC a compile-time-validated cross-project reference that enforces access tiers and contracts.
# MAGIC
# MAGIC **In Lakeflow, there is no equivalent of this.** To give the marketing and finance teams
# MAGIC their own governed, team-scoped datasets, you would need to do what this notebook does:
# MAGIC build a separate DLT pipeline for each team, where:
# MAGIC
# MAGIC - Each team reads from the shared gold tables using **hardcoded table strings** (`spark.read.table(...)`)
# MAGIC   with no compile-time validation — if the upstream table is renamed or a column is dropped,
# MAGIC   this fails at **runtime**, not at build time
# MAGIC - Business logic (e.g. customer segmentation thresholds) is **re-defined** in each team's pipeline
# MAGIC   because there is no `access: protected` concept — any team can read any table, but they
# MAGIC   cannot inherit or enforce a shared definition
# MAGIC - Column metadata (comments) must be **manually repeated** in each pipeline's `@dlt.table(comment=...)`
# MAGIC   — there is no `persist_docs` that automatically propagates from a central definition
# MAGIC - There is no **contract enforcement** — if the platform team changes `gold_dim_customers`
# MAGIC   to rename `customer_segment` to `segment_tier`, this pipeline breaks silently at next run
# MAGIC
# MAGIC ## Side-by-side comparison
# MAGIC
# MAGIC | | dbt Mesh | Lakeflow equivalent (this notebook) |
# MAGIC |---|---|---|
# MAGIC | How marketing reads platform data | `{{ ref('platform', 'fct_orders') }}` | `spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")` |
# MAGIC | Validation of that reference | Compile-time — job fails before SQL runs | Runtime — pipeline fails when it executes |
# MAGIC | Who can consume platform models | Only teams that ref `public` models | Any team — no access tier enforcement |
# MAGIC | Breaking change detection | Contract enforced at build — `ERROR: column removed` | Silent until next pipeline run |
# MAGIC | Customer segmentation logic | Defined once in `platform/dim_customers.sql`, inherited | Re-defined in each team's pipeline (see below) |
# MAGIC | Column metadata | Auto-pushed by `persist_docs` | Manually written per table per pipeline |
# MAGIC | Shared metric definitions | `_semantic_models.yml` — one source of truth | Duplicated SQL in each team's gold table |
# MAGIC
# MAGIC ## How to run this notebook
# MAGIC
# MAGIC This requires two separate DLT pipelines — one per consumer team.
# MAGIC **Run `01_lakeflow_pipeline.py` first** — this notebook reads from its gold output.
# MAGIC
# MAGIC **Pipeline 1 — Marketing:**
# MAGIC 1. Workflows → Delta Live Tables → Create Pipeline
# MAGIC 2. Name: `ecommerce-lakeflow-marketing`
# MAGIC 3. Source: this notebook (section: Marketing Pipeline)
# MAGIC 4. Target catalog: `enablement`, Target schema: `ecommerce_lakeflow_marketing`
# MAGIC
# MAGIC **Pipeline 2 — Finance:**
# MAGIC Same steps, name: `ecommerce-lakeflow-finance`, schema: `ecommerce_lakeflow_finance`
# MAGIC
# MAGIC In practice you would split these into two notebooks. They are combined here
# MAGIC to make the duplication visible in a single scroll.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Marketing Pipeline
# MAGIC ### `ecommerce_lakeflow_marketing` schema
# MAGIC
# MAGIC Goal: replicate what `marketing/models/mart_customer_segments.sql` and
# MAGIC `marketing/models/mart_country_performance.sql` do in dbt Mesh.
# MAGIC
# MAGIC **Notice:** the customer segmentation thresholds (`>= 500`, `>= 100`) are
# MAGIC copy-pasted from `01_lakeflow_pipeline.py` → `gold_dim_customers`. There is
# MAGIC no mechanism to reference the platform definition — it must be duplicated.
# MAGIC If the platform team changes the threshold, this pipeline will silently compute
# MAGIC different segments until someone notices the discrepancy.

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, round as _round,
    when, coalesce, lit, datediff, current_date,
    max as _max
)

# Source catalog/schema for upstream gold tables — set via DLT pipeline configuration.
SOURCE_CATALOG = spark.conf.get("source_catalog", "enablement")
SOURCE_LF_SCHEMA = spark.conf.get("source_lakeflow_schema", "ecommerce_lakeflow")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Reading from the shared gold layer
# MAGIC
# MAGIC In dbt Mesh, this would be:
# MAGIC ```sql
# MAGIC -- marketing/models/mart_customer_segments.sql
# MAGIC with customers as (
# MAGIC     select * from {{ ref('platform', 'dim_customers') }}   -- compile-time validated
# MAGIC ),
# MAGIC orders as (
# MAGIC     select * from {{ ref('platform', 'fct_orders') }}      -- access: public enforced
# MAGIC )
# MAGIC ```
# MAGIC
# MAGIC In Lakeflow, this is a hardcoded string. If the table is renamed, moved, or
# MAGIC a column is dropped, the pipeline fails at runtime with no prior warning.

# COMMAND ----------

@dlt.table(
    name="marketing_customer_segments",
    comment="""
        Customer segments for the marketing team.
        Segments: champion (ordered recently + high value), loyal (frequent buyer),
        at_risk (high value but not recent), lapsed (>90 days since last order),
        never_purchased, other.

        NOTE: Segment thresholds are duplicated from the platform gold pipeline.
        If the platform team changes the definition of 'high_value' (currently >= $500),
        this table will be inconsistent until manually updated.

        dbt Mesh equivalent: marketing.mart_customer_segments
        reads from: enablement.ecommerce_lakeflow.gold_dim_customers (hardcoded string)
    """,
    table_properties={"quality": "gold", "team": "marketing"}
)
def marketing_customer_segments():
    # Read from the platform pipeline's gold output via hardcoded table path.
    # There is no ref() — no compile-time validation, no access control.
    customers = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_dim_customers")
    orders    = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")

    # Latest order date per customer — needed for recency calculation
    recency = (
        orders
        .groupBy("customer_id")
        .agg(_max("order_date").alias("last_order_date"))
    )

    enriched = customers.join(recency, "customer_id", "left")

    # DUPLICATION ALERT: these thresholds are also defined in gold_dim_customers.
    # high_value = total_lifetime_value >= 500
    # mid_value  = total_lifetime_value >= 100
    # There is no single source of truth — both places must be kept in sync manually.
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
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "country",
            "customer_segment",     # from platform — duplicated definition
            "total_lifetime_value",
            "number_of_orders",
            "last_order_date",
            "days_since_last_order",
            "marketing_segment"
        )
    )

# COMMAND ----------

@dlt.table(
    name="marketing_country_performance",
    comment="""
        Revenue and customer metrics by country for the marketing team.
        Revenue = amount_paid on completed orders only.

        NOTE: The 'completed orders only' filter is also in platform's gold_fct_revenue.
        If the platform team changes the revenue recognition rule, this table must be
        updated separately. There is no contract that enforces consistency.

        dbt Mesh equivalent: marketing.mart_country_performance
        reads from: enablement.ecommerce_lakeflow.gold_fct_orders (hardcoded)
                    enablement.ecommerce_lakeflow.gold_dim_customers (hardcoded)
    """,
    table_properties={"quality": "gold", "team": "marketing"}
)
def marketing_country_performance():
    orders    = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")
    customers = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_dim_customers")

    completed = orders.filter(col("status") == "completed")

    order_with_country = completed.join(
        customers.select("customer_id", "country"),
        "customer_id"
    )

    return (
        order_with_country
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

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Finance Pipeline
# MAGIC ### `ecommerce_lakeflow_finance` schema
# MAGIC
# MAGIC Goal: replicate what `finance/models/fct_revenue.sql` and
# MAGIC `finance/models/fct_revenue_by_product.sql` do in dbt Mesh.
# MAGIC
# MAGIC **Notice:** `gold_fct_revenue` already exists in the platform pipeline.
# MAGIC The finance team either re-reads it (hardcoded string, no validation) or
# MAGIC re-builds the revenue logic themselves. Both options create divergence risk.
# MAGIC
# MAGIC In dbt Mesh, `finance/models/fct_revenue.sql` is 8 lines:
# MAGIC ```sql
# MAGIC select order_id, order_date, customer_id, status, amount_paid,
# MAGIC        case when status = 'completed' then amount_paid else 0 end as recognised_revenue,
# MAGIC        date_trunc('month', order_date) as revenue_month
# MAGIC from {{ ref('platform', 'fct_orders') }}   -- one validated ref, contract enforced
# MAGIC ```
# MAGIC The equivalent below is longer and contains a copy of the business rule.

# COMMAND ----------

@dlt.table(
    name="finance_fct_revenue",
    comment="""
        Revenue fact table for the finance team.
        recognised_revenue = amount_paid for completed orders, 0 otherwise.

        NOTE: Revenue recognition rule (status = 'completed') is duplicated from
        the platform pipeline. If the platform team adds a new status (e.g. 'partially_refunded'),
        finance will not see it here until this pipeline is manually updated.

        dbt Mesh equivalent: finance.fct_revenue
        reads from: enablement.ecommerce_lakeflow.gold_fct_orders (hardcoded)
    """,
    table_properties={"quality": "gold", "team": "finance"}
)
def finance_fct_revenue():
    # Hardcoded ref — no validation, no access tier, no contract.
    orders = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")

    return (
        orders
        .select(
            col("order_id"),
            col("order_date"),
            col("customer_id"),
            col("status"),
            col("amount_paid"),
            # DUPLICATION: revenue recognition rule also lives in gold_fct_revenue.
            # Two tables now encode the same business rule independently.
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
        Revenue broken down by product category for the finance team.

        NOTE: Product join logic is duplicated — the platform pipeline does not
        expose a product-enriched orders table as a public model (it would be
        marked access: protected in dbt). The finance team must join themselves,
        re-implementing logic the platform team may also have internally.

        If the platform team renames a column in gold_dim_customers or changes
        gold_fct_orders, this table fails at runtime with no prior warning.

        dbt Mesh equivalent: finance.fct_revenue_by_product
        reads from: enablement.ecommerce_lakeflow.gold_fct_orders (hardcoded)
                    enablement.ecommerce_lakeflow.silver_products (hardcoded — accessing silver directly!)
    """,
    table_properties={"quality": "gold", "team": "finance"}
)
def finance_fct_revenue_by_product():
    orders   = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_LF_SCHEMA}.gold_fct_orders")
    # No product-level gold table exists in the platform pipeline,
    # so finance must reach into silver — bypassing any gold-layer curation.
    # In dbt Mesh, staging models are access: protected and cannot be referenced
    # by consumer projects. In Lakeflow, there is no such restriction.
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

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## What you just built — and why it matters for the demo
# MAGIC
# MAGIC This notebook creates **6 tables** across 2 schemas (`ecommerce_lakeflow_marketing`,
# MAGIC `ecommerce_lakeflow_finance`) that are the Lakeflow equivalent of the 4 models
# MAGIC in the dbt Mesh consumer projects.
# MAGIC
# MAGIC ### The problems embedded in this notebook (use these in the demo)
# MAGIC
# MAGIC 1. **Duplication of business logic**
# MAGIC    Search this file for "DUPLICATION". The customer segmentation thresholds
# MAGIC    (`>= 500` for high_value) appear in both `01_lakeflow_pipeline.py` and here.
# MAGIC    The revenue recognition rule (`status = 'completed'`) appears in both the
# MAGIC    platform pipeline and `finance_fct_revenue`. Two teams, two definitions —
# MAGIC    one incident away from diverging.
# MAGIC
# MAGIC 2. **Hardcoded table references — no compile-time safety**
# MAGIC    Every `spark.read.table(...)` call is a string. If the platform team renames
# MAGIC    a table or removes a column, these pipelines fail at runtime. In dbt Cloud,
# MAGIC    the `platform - full build` job would fail immediately when the contract is
# MAGIC    violated — before any consumer is affected.
# MAGIC
# MAGIC 3. **No access tiers — consumer bypasses protected layers**
# MAGIC    `finance_fct_revenue_by_product` reads from `silver_products` directly
# MAGIC    because no product-level gold table exists. In dbt Mesh, silver is
# MAGIC    `access: protected` — the finance project literally cannot compile a ref to it.
# MAGIC    In Lakeflow, there is no enforcement: any team can read any table.
# MAGIC
# MAGIC 4. **Metadata is not inherited — it must be repeated**
# MAGIC    Every `@dlt.table(comment=...)` above had to be manually written for this team's
# MAGIC    tables. In dbt Mesh, `persist_docs` runs on every job and automatically
# MAGIC    propagates the platform's column descriptions into Unity Catalog.
# MAGIC    Here, if the platform team updates a column description, nothing propagates.
# MAGIC
# MAGIC 5. **Two pipelines to maintain instead of two projects**
# MAGIC    The marketing and finance teams each own a pipeline that depends on the main
# MAGIC    pipeline having run first — but there is no formal dependency declaration.
# MAGIC    If the platform pipeline fails or is delayed, the consumer pipelines will
# MAGIC    either fail or silently read stale data. In dbt Cloud, project dependencies
# MAGIC    are declared in `dependencies.yml` and enforced by the scheduler.
# MAGIC
# MAGIC ### The demo question
# MAGIC
# MAGIC Show this notebook alongside the 8-line `finance/models/fct_revenue.sql`:
# MAGIC
# MAGIC > "Both approaches produce the same tables in Unity Catalog.
# MAGIC >  One is 8 lines with a compile-time-validated ref and an enforced contract.
# MAGIC >  The other is 200 lines with five manual duplication points and no safety net.
# MAGIC >  Which one would you rather maintain at 2am when the payment pipeline breaks?"
