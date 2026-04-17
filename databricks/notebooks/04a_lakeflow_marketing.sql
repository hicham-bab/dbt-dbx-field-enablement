-- Lakeflow — Marketing Team Consumer Pipeline (SQL version)
--
-- This is what the marketing team would need to build and maintain in Lakeflow
-- to get their own governed dataset on top of the platform gold tables.
--
-- In dbt Mesh, the equivalent is marketing/models/mart_customer_segments.sql:
--   select * from {{ ref('platform', 'dim_customers') }}  -- compile-time validated
--   select * from {{ ref('platform', 'fct_orders') }}     -- access: public enforced
--
-- Here, those refs are hardcoded table strings. Same SQL language, completely
-- different safety net.
--
-- Run 01_lakeflow_pipeline.py first — this reads from its gold output.
--
-- Pipeline configuration:
--   Jobs & Pipelines → Create → ETL pipeline
--   Name: ecommerce-lakeflow-marketing
--   Catalog: enablement, Schema: ecommerce_lakeflow_marketing
--   Add existing assets → select this file

-- =============================================================================
-- Table 1: marketing_customer_segments
--
-- dbt Mesh equivalent: marketing.mart_customer_segments (8 lines + ref())
-- Lakeflow reads from: ${source_catalog}.${source_lakeflow_schema}.gold_* (hardcoded strings)
--
-- DUPLICATION: The customer segmentation thresholds below (>= 500, >= 100)
-- are also defined in 01_lakeflow_pipeline.py → gold_dim_customers.
-- There is no mechanism to share or inherit this definition across pipelines.
-- If the platform team changes the threshold, this view silently diverges.
-- =============================================================================

CREATE OR REFRESH MATERIALIZED VIEW marketing_customer_segments
COMMENT "Customer segments for the marketing team.
Segments: champion (high value + ordered recently), loyal (3+ orders),
at_risk (high value but inactive > 60 days), lapsed (inactive > 90 days),
never_purchased, other.

NOTE: Segment thresholds duplicated from gold_dim_customers in the platform pipeline.
dbt Mesh equivalent: marketing.mart_customer_segments (validated ref, contract enforced)
Reads from: ${source_catalog}.${source_lakeflow_schema}.gold_dim_customers (hardcoded — no validation)"
AS
WITH order_recency AS (
  -- Hardcoded table path. In dbt Mesh: {{ ref('platform', 'fct_orders') }}
  -- If this table is renamed or a column dropped, this fails at runtime, not build time.
  SELECT
    customer_id,
    MAX(order_date)  AS last_order_date,
    COUNT(order_id)  AS order_count
  FROM ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders
  GROUP BY customer_id
)
SELECT
  c.customer_id,
  c.first_name,
  c.last_name,
  c.email,
  c.country,
  c.customer_segment,        -- duplicated definition from platform pipeline
  c.total_lifetime_value,
  c.number_of_orders,
  r.last_order_date,
  datediff(current_date(), r.last_order_date) AS days_since_last_order,
  -- DUPLICATION: >= 500 / >= 100 also defined in gold_dim_customers.
  -- Two pipelines, two independent definitions, zero enforcement.
  CASE
    WHEN c.total_lifetime_value >= 500
     AND datediff(current_date(), r.last_order_date) <= 30  THEN 'champion'
    WHEN c.number_of_orders >= 3                            THEN 'loyal'
    WHEN c.total_lifetime_value >= 100
     AND datediff(current_date(), r.last_order_date) > 60   THEN 'at_risk'
    WHEN datediff(current_date(), r.last_order_date) > 90   THEN 'lapsed'
    WHEN c.number_of_orders = 0                             THEN 'never_purchased'
    ELSE 'other'
  END AS marketing_segment
-- Hardcoded table path. In dbt Mesh: {{ ref('platform', 'dim_customers') }}
FROM ${source_catalog}.${source_lakeflow_schema}.gold_dim_customers c
LEFT JOIN order_recency r ON c.customer_id = r.customer_id;


-- =============================================================================
-- Table 2: marketing_country_performance
--
-- dbt Mesh equivalent: marketing.mart_country_performance (validated ref)
-- Lakeflow reads from: ${source_catalog}.${source_lakeflow_schema}.gold_* (hardcoded strings)
--
-- DUPLICATION: The 'completed orders only' revenue filter is also defined in
-- gold_fct_revenue in the platform pipeline. If the platform team changes
-- revenue recognition logic, this must be updated separately.
-- =============================================================================

CREATE OR REFRESH MATERIALIZED VIEW marketing_country_performance
COMMENT "Revenue and customer metrics by country for the marketing team.
Revenue = amount_paid on completed orders only.

NOTE: Revenue recognition rule (status = 'completed') duplicated from platform pipeline.
dbt Mesh equivalent: marketing.mart_country_performance (validated ref, contract enforced)
Reads from: ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders (hardcoded — no validation)"
AS
WITH completed_orders AS (
  -- DUPLICATION: 'completed' filter also in gold_fct_revenue (platform pipeline).
  -- Hardcoded table path. In dbt Mesh: {{ ref('platform', 'fct_orders') }}
  SELECT
    o.order_id,
    o.customer_id,
    o.amount_paid
  FROM ${source_catalog}.${source_lakeflow_schema}.gold_fct_orders o
  WHERE o.status = 'completed'
)
SELECT
  c.country,
  COUNT(DISTINCT o.order_id)    AS total_orders,
  ROUND(SUM(o.amount_paid), 2)  AS total_revenue,
  ROUND(AVG(o.amount_paid), 2)  AS avg_order_value,
  COUNT(DISTINCT o.customer_id) AS active_customers,
  ROUND(
    SUM(o.amount_paid) / NULLIF(COUNT(DISTINCT o.customer_id), 0),
  2)                            AS revenue_per_customer
-- Hardcoded table path. In dbt Mesh: {{ ref('platform', 'dim_customers') }}
FROM completed_orders o
JOIN ${source_catalog}.${source_lakeflow_schema}.gold_dim_customers c ON o.customer_id = c.customer_id
GROUP BY c.country
ORDER BY total_revenue DESC;
