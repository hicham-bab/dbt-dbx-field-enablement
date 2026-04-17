-- Lakeflow (Delta Live Tables) — E-Commerce Platform Pipeline (SQL version)
--
-- What this shows dbt field teams:
-- - How Databricks solves the same medallion pattern problem natively, in SQL
-- - DLT declarative SQL syntax vs dbt SQL models — similar syntax, different governance
-- - What DLT has: auto-lineage, auto-retry, expectations (data quality)
-- - What DLT doesn't have: ref(), version-controlled docs, test suite, contracts, CI/CD
--
-- Pipeline configuration:
-- 1. Jobs & Pipelines → Create → ETL pipeline
-- 2. In the dialog: name = ecommerce-lakeflow-demo, catalog = <your_catalog>, schema = <your_schema>_lakeflow → Create
-- 3. In pipeline settings → Configuration, add: source_catalog = <your_catalog>, source_schema = <your_schema>
-- 4. On the "Next step" screen → Add existing assets → select this file → Add
-- 5. Click Start — creates all 13 tables (5 bronze + 5 silver + 3 gold)


-- =============================================================================
-- BRONZE LAYER — Raw Ingestion
--
-- Bronze tables ingest raw data as-is from source tables.
-- No transformations, no cleaning.
--
-- dbt equivalent: source() declarations in _sources.yml
-- Key difference: dbt sources have freshness checks (dbt source freshness),
-- loaded_at_field tracking, and warn/error thresholds defined in code.
-- DLT has no equivalent — you would need a custom monitoring notebook.
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_customers
COMMENT "Raw customer data ingested from source system. No transformations applied."
TBLPROPERTIES ("quality" = "bronze")
AS SELECT * FROM STREAM(${source_catalog}.${source_schema}.raw_customers);

CREATE OR REFRESH STREAMING TABLE bronze_orders
COMMENT "Raw order records ingested from source system. No transformations applied."
TBLPROPERTIES ("quality" = "bronze")
AS SELECT * FROM STREAM(${source_catalog}.${source_schema}.raw_orders);

CREATE OR REFRESH STREAMING TABLE bronze_order_items
COMMENT "Raw order line items ingested from source system. No transformations applied."
TBLPROPERTIES ("quality" = "bronze")
AS SELECT * FROM STREAM(${source_catalog}.${source_schema}.raw_order_items);

CREATE OR REFRESH STREAMING TABLE bronze_products
COMMENT "Raw product catalog ingested from source system. No transformations applied."
TBLPROPERTIES ("quality" = "bronze")
AS SELECT * FROM STREAM(${source_catalog}.${source_schema}.raw_products);

CREATE OR REFRESH STREAMING TABLE bronze_payments
COMMENT "Raw payment transactions ingested from source system. No transformations applied."
TBLPROPERTIES ("quality" = "bronze")
AS SELECT * FROM STREAM(${source_catalog}.${source_schema}.raw_payments);


-- =============================================================================
-- SILVER LAYER — Cleaned and Standardised
--
-- dbt equivalent: staging models with column-level transformations and tests.
--
-- Key differences from dbt:
-- - DLT CONSTRAINT = dbt test, but only 3 options: warn, drop row, or fail pipeline
-- - dbt has 4 built-in tests + unlimited custom SQL tests + dbt_expectations package
-- - DLT constraints are defined in Python or SQL inline — no separate YAML test file
-- - No auto-generated docs from constraints (dbt generates a full docs site)
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE silver_customers
  (CONSTRAINT valid_customer_id EXPECT (customer_id IS NOT NULL) ON VIOLATION DROP ROW,
   CONSTRAINT valid_email       EXPECT (email IS NOT NULL))
COMMENT "Cleaned and standardised customer records. Nulls on customer_id dropped."
TBLPROPERTIES ("quality" = "silver")
AS
SELECT
  customer_id,
  first_name,
  last_name,
  lower(email)   AS email,
  to_date(created_at) AS created_date,
  upper(country) AS country
FROM STREAM(LIVE.bronze_customers);

CREATE OR REFRESH STREAMING TABLE silver_orders
  (CONSTRAINT valid_order_id EXPECT (order_id IS NOT NULL) ON VIOLATION DROP ROW,
   CONSTRAINT valid_status   EXPECT (status IN ('placed', 'shipped', 'completed', 'returned')))
COMMENT "Cleaned orders with standardised status values."
TBLPROPERTIES ("quality" = "silver")
AS
SELECT
  order_id,
  customer_id,
  lower(status)        AS status,
  to_date(order_date)  AS order_date,
  amount
FROM STREAM(LIVE.bronze_orders);

CREATE OR REFRESH STREAMING TABLE silver_order_items
  (CONSTRAINT valid_item_id       EXPECT (order_item_id IS NOT NULL) ON VIOLATION DROP ROW,
   CONSTRAINT positive_quantity   EXPECT (quantity > 0))
COMMENT "Cleaned order line items with validated quantities and computed line total."
TBLPROPERTIES ("quality" = "silver")
AS
SELECT
  order_item_id,
  order_id,
  product_id,
  quantity,
  unit_price,
  quantity * unit_price AS line_total
FROM STREAM(LIVE.bronze_order_items);

CREATE OR REFRESH STREAMING TABLE silver_products
  (CONSTRAINT valid_product_id EXPECT (product_id IS NOT NULL) ON VIOLATION DROP ROW)
COMMENT "Cleaned product catalog."
TBLPROPERTIES ("quality" = "silver")
AS
SELECT
  product_id,
  product_name,
  lower(category) AS category,
  unit_price,
  is_active
FROM STREAM(LIVE.bronze_products);

CREATE OR REFRESH STREAMING TABLE silver_payments
  (CONSTRAINT valid_payment_id EXPECT (payment_id IS NOT NULL) ON VIOLATION DROP ROW,
   CONSTRAINT positive_amount  EXPECT (amount > 0))
COMMENT "Cleaned payment records with standardised payment method and status."
TBLPROPERTIES ("quality" = "silver")
AS
SELECT
  payment_id,
  order_id,
  lower(payment_method) AS payment_method,
  amount,
  to_date(payment_date) AS payment_date,
  lower(status)         AS payment_status
FROM STREAM(LIVE.bronze_payments);


-- =============================================================================
-- GOLD LAYER — Business Entities
--
-- dbt equivalent: mart models (dim_customers, fct_orders, fct_revenue)
--
-- Key differences from dbt:
-- - dbt marts have enforced contracts (data_type on every column) — if a column
--   type changes, the build fails before consumers are affected
-- - dbt marts have access: public — only explicitly public models can be
--   referenced by consumer projects (dbt Mesh)
-- - dbt docs are auto-generated from YAML, pushed to Unity Catalog via persist_docs
-- - No contract enforcement here — schema changes break consumers silently
-- =============================================================================

CREATE OR REFRESH MATERIALIZED VIEW gold_dim_customers
COMMENT "Customer dimension with lifetime value metrics and segmentation.
customer_segment: high_value >= 500, mid_value >= 100, low_value < 100.
NOTE: No contract enforcement — if this schema changes, consumer pipelines
break at runtime. In dbt Mesh, a contract violation fails the build immediately."
TBLPROPERTIES ("quality" = "gold")
AS
WITH order_metrics AS (
  SELECT
    customer_id,
    COUNT(order_id)  AS number_of_orders,
    MIN(order_date)  AS first_order_date,
    MAX(order_date)  AS most_recent_order_date
  FROM LIVE.silver_orders
  GROUP BY customer_id
),
payment_totals AS (
  SELECT
    o.customer_id,
    ROUND(SUM(p.amount), 2) AS total_lifetime_value
  FROM LIVE.silver_payments p
  JOIN LIVE.silver_orders o ON p.order_id = o.order_id
  WHERE p.payment_status = 'success'
  GROUP BY o.customer_id
)
SELECT
  c.customer_id,
  c.first_name,
  c.last_name,
  c.email,
  c.country,
  c.created_date,
  COALESCE(om.number_of_orders,      0)    AS number_of_orders,
  om.first_order_date,
  om.most_recent_order_date,
  COALESCE(pt.total_lifetime_value,  0.0)  AS total_lifetime_value,
  CASE
    WHEN COALESCE(pt.total_lifetime_value, 0) >= 500 THEN 'high_value'
    WHEN COALESCE(pt.total_lifetime_value, 0) >= 100 THEN 'mid_value'
    ELSE 'low_value'
  END AS customer_segment
FROM LIVE.silver_customers c
LEFT JOIN order_metrics  om ON c.customer_id = om.customer_id
LEFT JOIN payment_totals pt ON c.customer_id = pt.customer_id;


CREATE OR REFRESH MATERIALIZED VIEW gold_fct_orders
COMMENT "Order fact table enriched with item counts and successful payment totals.
amount_paid: sum of successful payments for this order.
NOTE: No contract enforcement — schema changes silently break consumer pipelines."
TBLPROPERTIES ("quality" = "gold")
AS
WITH item_metrics AS (
  SELECT
    order_id,
    COUNT(order_item_id)   AS number_of_items,
    SUM(line_total)        AS items_total
  FROM LIVE.silver_order_items
  GROUP BY order_id
),
payment_metrics AS (
  SELECT
    order_id,
    SUM(amount) AS amount_paid
  FROM LIVE.silver_payments
  WHERE payment_status = 'success'
  GROUP BY order_id
)
SELECT
  o.order_id,
  o.customer_id,
  o.status,
  o.order_date,
  o.amount,
  COALESCE(im.number_of_items, 0)   AS number_of_items,
  COALESCE(im.items_total,     0.0) AS items_total,
  COALESCE(pm.amount_paid,     0.0) AS amount_paid
FROM LIVE.silver_orders o
LEFT JOIN item_metrics   im ON o.order_id = im.order_id
LEFT JOIN payment_metrics pm ON o.order_id = pm.order_id;


CREATE OR REFRESH MATERIALIZED VIEW gold_fct_revenue
COMMENT "Daily revenue aggregates for completed orders only.
daily_revenue: total successful payments on completed orders for the day."
TBLPROPERTIES ("quality" = "gold")
AS
SELECT
  order_date,
  date_format(order_date, 'yyyy-MM')    AS revenue_month,
  SUM(amount_paid)                       AS daily_revenue,
  COUNT(order_id)                        AS number_of_orders,
  ROUND(AVG(amount_paid), 2)             AS avg_order_value
FROM LIVE.gold_fct_orders
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date;
