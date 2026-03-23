-- =============================================================================
-- Databricks Metric Views — E-Commerce Demo
-- =============================================================================
-- Run this in the Databricks SQL Editor after running 00_setup_raw_data.py
-- and building the dbt platform project.
--
-- Creates metric views in enablement.ecommerce_metric_views that mirror
-- the same metrics defined in platform/models/semantic/_semantic_models.yml.
-- This enables an apples-to-apples comparison in the demo.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS enablement.ecommerce_metric_views;

-- -----------------------------------------------------------------------------
-- Metric: total_revenue
-- Same definition as _semantic_models.yml: total_recognised_revenue metric
-- (completed orders only)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.total_revenue AS
SELECT
    SUM(amount_paid) AS total_revenue
FROM enablement.ecommerce.fct_orders
WHERE status = 'completed';

-- -----------------------------------------------------------------------------
-- Metric: avg_order_value
-- Same as avg_order_value metric in semantic layer
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.avg_order_value AS
SELECT
    AVG(amount_paid) AS avg_order_value
FROM enablement.ecommerce.fct_orders
WHERE status = 'completed';

-- -----------------------------------------------------------------------------
-- Metric: total_orders
-- Count of all orders (all statuses) — same as total_orders metric
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.total_orders AS
SELECT
    COUNT(DISTINCT order_id) AS total_orders
FROM enablement.ecommerce.fct_orders;

-- -----------------------------------------------------------------------------
-- Metric: return_rate
-- Returned orders / total orders — same as return_rate ratio metric
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.return_rate AS
SELECT
    COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END) AS returned_orders,
    COUNT(DISTINCT order_id)                                         AS total_orders,
    COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
        / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100     AS return_rate_pct
FROM enablement.ecommerce.fct_orders;

-- -----------------------------------------------------------------------------
-- Metric: customer_count
-- Distinct customers — same as total_customers metric
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.customer_count AS
SELECT
    COUNT(DISTINCT customer_id) AS customer_count
FROM enablement.ecommerce.dim_customers;

-- -----------------------------------------------------------------------------
-- Metric: avg_lifetime_value
-- Average customer LTV — same as avg_customer_lifetime_value metric
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.avg_lifetime_value AS
SELECT
    AVG(total_lifetime_value) AS avg_lifetime_value
FROM enablement.ecommerce.dim_customers;

-- -----------------------------------------------------------------------------
-- Combined dashboard view for side-by-side comparison in the Streamlit app
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.all_metrics AS
SELECT
    SUM(CASE WHEN o.status = 'completed' THEN o.amount_paid ELSE 0 END) AS total_revenue,
    AVG(CASE WHEN o.status = 'completed' THEN o.amount_paid END)         AS avg_order_value,
    COUNT(DISTINCT o.order_id)                                           AS total_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'returned' THEN o.order_id END)
        / CAST(COUNT(DISTINCT o.order_id) AS DECIMAL(10,4)) * 100       AS return_rate_pct,
    COUNT(DISTINCT c.customer_id)                                        AS customer_count,
    AVG(c.total_lifetime_value)                                          AS avg_lifetime_value
FROM enablement.ecommerce.fct_orders o
CROSS JOIN (SELECT AVG(total_lifetime_value) AS total_lifetime_value,
                   COUNT(DISTINCT customer_id) AS customer_id
            FROM enablement.ecommerce.dim_customers) c;

-- Verify
SELECT 'total_revenue'    AS metric, CAST(total_revenue    AS STRING) AS value FROM enablement.ecommerce_metric_views.total_revenue
UNION ALL
SELECT 'avg_order_value',  CAST(avg_order_value  AS STRING) FROM enablement.ecommerce_metric_views.avg_order_value
UNION ALL
SELECT 'total_orders',     CAST(total_orders     AS STRING) FROM enablement.ecommerce_metric_views.total_orders
UNION ALL
SELECT 'customer_count',   CAST(customer_count   AS STRING) FROM enablement.ecommerce_metric_views.customer_count
UNION ALL
SELECT 'avg_ltv',          CAST(avg_lifetime_value AS STRING) FROM enablement.ecommerce_metric_views.avg_lifetime_value;
