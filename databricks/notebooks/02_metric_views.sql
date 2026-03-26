-- =============================================================================
-- Databricks Metric Views — Verification Queries
-- =============================================================================
--
-- Metric Views are defined in YAML, not SQL DDL.
-- Use these files to create them in the Databricks UI:
--   databricks/notebooks/02a_metric_view_orders.yml    → orders_metrics
--   databricks/notebooks/02b_metric_view_customers.yml → customer_metrics
--
-- HOW TO CREATE A METRIC VIEW:
--   1. In Databricks: New → Metric view (or Catalog → Create → Metric view)
--   2. Paste the YAML from 02a_metric_view_orders.yml into the definition editor
--   3. Save — Databricks stores the definition and registers it in Unity Catalog
--   4. Repeat for 02b_metric_view_customers.yml
--
-- Run the queries below AFTER creating both metric views to verify they work.
-- =============================================================================


-- Verify the dbt source tables exist (required before metric views will resolve)
SHOW TABLES IN enablement.ecommerce;


-- Spot-check: total revenue should match the dbt semantic layer metric
SELECT
  SUM(CASE WHEN status = 'completed' THEN amount_paid ELSE 0 END) AS total_revenue,
  COUNT(DISTINCT order_id)                                         AS total_orders,
  COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
    / CAST(COUNT(DISTINCT order_id) AS DOUBLE) * 100              AS return_rate_pct
FROM enablement.ecommerce.fct_orders;


-- Spot-check: customer metrics
SELECT
  customer_segment,
  COUNT(DISTINCT customer_id)     AS customer_count,
  ROUND(AVG(total_lifetime_value), 2) AS avg_ltv
FROM enablement.ecommerce.dim_customers
GROUP BY customer_segment
ORDER BY avg_ltv DESC;
