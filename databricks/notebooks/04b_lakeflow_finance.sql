-- Lakeflow — Finance Team Consumer Pipeline (SQL version)
--
-- This is what the finance team would need to build and maintain in Lakeflow
-- to get their own governed dataset on top of the platform gold tables.
--
-- In dbt Mesh, the equivalent is finance/models/fct_revenue.sql — 8 lines:
--   select order_id, order_date, customer_id, status, amount_paid,
--          case when status = 'completed' then amount_paid else 0 end as recognised_revenue,
--          date_trunc('month', order_date) as revenue_month
--   from {{ ref('platform', 'fct_orders') }}   -- one validated ref, contract enforced
--
-- The SQL below is longer and contains duplicated business logic.
-- Same language. No safety net.
--
-- Run 01_lakeflow_pipeline.py first — this reads from its gold output.
--
-- Pipeline configuration:
--   Jobs & Pipelines → Create → ETL pipeline
--   Name: ecommerce-lakeflow-finance
--   Catalog: enablement, Schema: ecommerce_lakeflow_finance
--   Add existing assets → select this file

-- =============================================================================
-- Table 1: finance_fct_revenue
--
-- dbt Mesh equivalent: finance.fct_revenue (8 lines, validated ref)
-- Lakeflow reads from: ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders (hardcoded)
--
-- DUPLICATION: The revenue recognition rule (status = 'completed') is also
-- defined in gold_fct_revenue in the platform pipeline. Two independent
-- definitions — one incident away from diverging.
-- =============================================================================

CREATE OR REFRESH MATERIALIZED VIEW finance_fct_revenue
COMMENT "Revenue fact table for the finance team.
recognised_revenue = amount_paid for completed orders, 0 otherwise.

NOTE: Revenue recognition rule duplicated from platform pipeline's gold_fct_revenue.
If the platform team adds a new status or changes the rule, finance must update
this pipeline manually — no contract links them.
dbt Mesh equivalent: finance.fct_revenue (8 lines, {{ ref('platform','fct_orders') }})
Reads from: ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders (hardcoded — no validation)"
AS
SELECT
  order_id,
  order_date,
  customer_id,
  status,
  amount_paid,
  -- DUPLICATION: this rule also lives in gold_fct_revenue (platform pipeline).
  -- In dbt Mesh this is one validated ref — here it is a copy.
  CASE
    WHEN status = 'completed' THEN amount_paid
    ELSE 0.0
  END                                            AS recognised_revenue,
  ROUND(amount_paid - COALESCE(items_total, 0), 2) AS payment_vs_items_delta,
  -- Hardcoded table path. In dbt Mesh: {{ ref('platform', 'fct_orders') }}
  date_trunc('month', order_date)                AS revenue_month
FROM ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders;


-- =============================================================================
-- Table 2: finance_fct_revenue_by_product
--
-- dbt Mesh equivalent: finance.fct_revenue_by_product (validated refs only to public models)
-- Lakeflow reads from: gold_fct_orders (hardcoded) + silver_products (hardcoded)
--
-- ACCESS TIER VIOLATION: No product-level gold table exists in the platform
-- pipeline, so finance reads directly from silver_products — bypassing the
-- gold layer entirely.
-- In dbt Mesh, staging/silver is access: protected. The finance project
-- cannot compile a ref to it — the build fails with "model is not public".
-- In Lakeflow there is no such enforcement: any team reads any layer freely.
-- =============================================================================

CREATE OR REFRESH MATERIALIZED VIEW finance_fct_revenue_by_product
COMMENT "Revenue by product category for the finance team.

NOTE: Reads from silver_products directly because no product-level gold table exists.
In dbt Mesh, staging models are access: protected — consumer projects cannot reference them.
In Lakeflow, there is no access tier enforcement across pipelines.
dbt Mesh equivalent: finance.fct_revenue_by_product (public models only)
Reads from: ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders (hardcoded)
            ${source_catalog}.${source_lakeflow_schema}.silver_products  (hardcoded — bypassing gold layer)"
AS
WITH completed AS (
  -- Hardcoded table path. In dbt Mesh: {{ ref('platform', 'fct_orders') }}
  SELECT order_id, customer_id, amount_paid
  FROM ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders
  WHERE status = 'completed'
),
products AS (
  -- Bypassing the gold layer — reading silver directly.
  -- In dbt Mesh this is impossible: silver/staging is access: protected.
  -- Any attempt to ref() it from a consumer project fails at compile time.
  SELECT product_id, product_name, category
  FROM ${source_catalog}.${source_lakeflow_schema}.silver_products
)
SELECT
  p.category,
  p.product_name,
  COUNT(o.order_id)            AS total_orders,
  ROUND(SUM(o.amount_paid), 2) AS total_revenue,
  ROUND(AVG(o.amount_paid), 2) AS avg_order_value
FROM completed o
CROSS JOIN products p
GROUP BY p.category, p.product_name
ORDER BY total_revenue DESC;
