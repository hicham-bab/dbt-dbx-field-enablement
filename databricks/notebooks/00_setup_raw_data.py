# Databricks notebook source
# MAGIC %md
# MAGIC # E-Commerce Demo — Raw Data Setup
# MAGIC
# MAGIC Run this notebook once to create the `enablement.ecommerce` catalog/schema
# MAGIC and load all five raw Delta tables used by both the dbt platform project
# MAGIC and the Lakeflow pipeline demo.
# MAGIC
# MAGIC Each table includes a `_loaded_at` TIMESTAMP column so that
# MAGIC `dbt source freshness` can check how recently each source was updated.
# MAGIC
# MAGIC **Expected row counts after setup:**
# MAGIC | Table | Rows |
# MAGIC |---|---|
# MAGIC | raw_customers | 10 |
# MAGIC | raw_orders | 15 |
# MAGIC | raw_order_items | 20 |
# MAGIC | raw_products | 10 |
# MAGIC | raw_payments | 15 |
# MAGIC
# MAGIC **Source freshness design:**
# MAGIC | Table | Updated by generator? | Freshness threshold |
# MAGIC |---|---|---|
# MAGIC | raw_customers | Yes (30 min schedule) | error after 6 hours |
# MAGIC | raw_orders | Yes (30 min schedule) | error after 6 hours |
# MAGIC | raw_order_items | Yes (30 min schedule) | error after 6 hours |
# MAGIC | raw_products | No (static catalog) | error after 7 days |
# MAGIC | raw_payments | **No — simulates stale payment feed** | **error after 2 days** |

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS enablement;
# MAGIC USE CATALOG enablement;
# MAGIC CREATE SCHEMA IF NOT EXISTS ecommerce;
# MAGIC USE SCHEMA ecommerce;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE enablement.ecommerce.raw_customers (
# MAGIC   customer_id   INT,
# MAGIC   first_name    STRING,
# MAGIC   last_name     STRING,
# MAGIC   email         STRING,
# MAGIC   created_at    DATE,
# MAGIC   country       STRING,
# MAGIC   _loaded_at    TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO enablement.ecommerce.raw_customers VALUES
# MAGIC   (1,  'Alice',  'Martin',  'alice.martin@example.com',  '2023-01-15', 'US', CURRENT_TIMESTAMP()),
# MAGIC   (2,  'Bob',    'Chen',    'bob.chen@example.com',      '2023-02-20', 'CA', CURRENT_TIMESTAMP()),
# MAGIC   (3,  'Clara',  'Nguyen',  'clara.nguyen@example.com',  '2023-03-05', 'US', CURRENT_TIMESTAMP()),
# MAGIC   (4,  'David',  'Osei',    'david.osei@example.com',    '2023-03-18', 'GB', CURRENT_TIMESTAMP()),
# MAGIC   (5,  'Eva',    'Rossi',   'eva.rossi@example.com',     '2023-04-01', 'IT', CURRENT_TIMESTAMP()),
# MAGIC   (6,  'Frank',  'Mueller', 'frank.mueller@example.com', '2023-04-22', 'DE', CURRENT_TIMESTAMP()),
# MAGIC   (7,  'Grace',  'Kim',     'grace.kim@example.com',     '2023-05-10', 'KR', CURRENT_TIMESTAMP()),
# MAGIC   (8,  'Hugo',   'Silva',   'hugo.silva@example.com',    '2023-06-03', 'BR', CURRENT_TIMESTAMP()),
# MAGIC   (9,  'Iris',   'Dubois',  'iris.dubois@example.com',   '2023-06-28', 'FR', CURRENT_TIMESTAMP()),
# MAGIC   (10, 'James',  'Patel',   'james.patel@example.com',   '2023-07-14', 'IN', CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE enablement.ecommerce.raw_orders (
# MAGIC   order_id       INT,
# MAGIC   customer_id    INT,
# MAGIC   order_date     DATE,
# MAGIC   status         STRING,
# MAGIC   amount         DECIMAL(10,2),
# MAGIC   payment_method STRING,
# MAGIC   _loaded_at     TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO enablement.ecommerce.raw_orders VALUES
# MAGIC   (1001,  1,  '2023-08-01', 'completed',  120.50, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1002,  2,  '2023-08-03', 'completed',   45.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1003,  3,  '2023-08-05', 'shipped',    310.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1004,  1,  '2023-08-07', 'completed',   89.99, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1005,  4,  '2023-08-10', 'returned',    55.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1006,  5,  '2023-08-12', 'completed',  670.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1007,  6,  '2023-08-14', 'placed',      29.99, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1008,  7,  '2023-08-15', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1009,  2,  '2023-08-18', 'completed',   88.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1010,  8,  '2023-08-20', 'shipped',    145.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1011,  3,  '2023-08-22', 'completed',  520.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1012,  9,  '2023-08-25', 'returned',    34.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1013, 10,  '2023-08-27', 'completed',  250.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1014,  1,  '2023-08-29', 'completed',   75.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1015,  5,  '2023-08-31', 'placed',     410.00, 'credit_card',   CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE enablement.ecommerce.raw_order_items (
# MAGIC   order_item_id INT,
# MAGIC   order_id      INT,
# MAGIC   product_id    INT,
# MAGIC   quantity      INT,
# MAGIC   unit_price    DECIMAL(10,2),
# MAGIC   _loaded_at    TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO enablement.ecommerce.raw_order_items VALUES
# MAGIC   (1,  1001, 101, 2,  35.00, CURRENT_TIMESTAMP()),
# MAGIC   (2,  1001, 103, 1,  50.50, CURRENT_TIMESTAMP()),
# MAGIC   (3,  1002, 102, 1,  45.00, CURRENT_TIMESTAMP()),
# MAGIC   (4,  1003, 104, 2,  80.00, CURRENT_TIMESTAMP()),
# MAGIC   (5,  1003, 105, 1, 150.00, CURRENT_TIMESTAMP()),
# MAGIC   (6,  1004, 101, 1,  35.00, CURRENT_TIMESTAMP()),
# MAGIC   (7,  1004, 106, 1,  54.99, CURRENT_TIMESTAMP()),
# MAGIC   (8,  1005, 102, 1,  55.00, CURRENT_TIMESTAMP()),
# MAGIC   (9,  1006, 107, 3,  90.00, CURRENT_TIMESTAMP()),
# MAGIC   (10, 1006, 104, 2,  80.00, CURRENT_TIMESTAMP()),
# MAGIC   (11, 1006, 108, 1, 320.00, CURRENT_TIMESTAMP()),
# MAGIC   (12, 1007, 103, 1,  29.99, CURRENT_TIMESTAMP()),
# MAGIC   (13, 1008, 109, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (14, 1009, 102, 1,  45.00, CURRENT_TIMESTAMP()),
# MAGIC   (15, 1009, 101, 1,  43.50, CURRENT_TIMESTAMP()),
# MAGIC   (16, 1010, 110, 1, 145.00, CURRENT_TIMESTAMP()),
# MAGIC   (17, 1011, 107, 2,  90.00, CURRENT_TIMESTAMP()),
# MAGIC   (18, 1011, 108, 1, 340.00, CURRENT_TIMESTAMP()),
# MAGIC   (19, 1012, 103, 1,  34.00, CURRENT_TIMESTAMP()),
# MAGIC   (20, 1013, 109, 1, 250.00, CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE enablement.ecommerce.raw_products (
# MAGIC   product_id   INT,
# MAGIC   product_name STRING,
# MAGIC   category     STRING,
# MAGIC   unit_price   DECIMAL(10,2),
# MAGIC   is_active    BOOLEAN,
# MAGIC   _loaded_at   TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO enablement.ecommerce.raw_products VALUES
# MAGIC   (101, 'Classic T-Shirt',            'apparel',     35.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (102, 'Running Shoes',               'footwear',    45.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (103, 'Wireless Earbuds',            'electronics', 29.99,  true, CURRENT_TIMESTAMP()),
# MAGIC   (104, 'Yoga Mat',                    'fitness',     80.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (105, 'Protein Powder',              'nutrition',  150.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (106, 'Denim Jacket',                'apparel',     54.99,  true, CURRENT_TIMESTAMP()),
# MAGIC   (107, 'Cycling Gloves',              'fitness',     90.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (108, 'Smart Watch',                 'electronics', 320.00, true, CURRENT_TIMESTAMP()),
# MAGIC   (109, 'Noise Cancelling Headphones', 'electronics', 250.00, true, CURRENT_TIMESTAMP()),
# MAGIC   (110, 'Trail Running Shoes',         'footwear',   145.00,  true, CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC -- raw_payments: seeded once, NOT updated by the data generator.
# MAGIC -- Simulates a third-party payment processor feed that has gone silent.
# MAGIC -- dbt source freshness will warn after 1 day and error after 2 days.
# MAGIC CREATE OR REPLACE TABLE enablement.ecommerce.raw_payments (
# MAGIC   payment_id     INT,
# MAGIC   order_id       INT,
# MAGIC   payment_method STRING,
# MAGIC   amount         DECIMAL(10,2),
# MAGIC   status         STRING,
# MAGIC   payment_date   DATE,
# MAGIC   _loaded_at     TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO enablement.ecommerce.raw_payments VALUES
# MAGIC   (2001, 1001, 'credit_card',   120.50, 'success', '2023-08-01', CURRENT_TIMESTAMP()),
# MAGIC   (2002, 1002, 'paypal',          45.00, 'success', '2023-08-03', CURRENT_TIMESTAMP()),
# MAGIC   (2003, 1003, 'credit_card',   310.00, 'success', '2023-08-05', CURRENT_TIMESTAMP()),
# MAGIC   (2004, 1004, 'credit_card',    89.99, 'success', '2023-08-07', CURRENT_TIMESTAMP()),
# MAGIC   (2005, 1005, 'bank_transfer',  55.00, 'success', '2023-08-10', CURRENT_TIMESTAMP()),
# MAGIC   (2006, 1005, 'bank_transfer',  55.00, 'failed',  '2023-08-11', CURRENT_TIMESTAMP()),
# MAGIC   (2007, 1006, 'credit_card',   670.00, 'success', '2023-08-12', CURRENT_TIMESTAMP()),
# MAGIC   (2008, 1007, 'paypal',          29.99, 'pending', '2023-08-14', CURRENT_TIMESTAMP()),
# MAGIC   (2009, 1008, 'credit_card',   199.00, 'success', '2023-08-15', CURRENT_TIMESTAMP()),
# MAGIC   (2010, 1009, 'paypal',          88.50, 'success', '2023-08-18', CURRENT_TIMESTAMP()),
# MAGIC   (2011, 1010, 'credit_card',   145.00, 'success', '2023-08-20', CURRENT_TIMESTAMP()),
# MAGIC   (2012, 1011, 'credit_card',   520.00, 'success', '2023-08-22', CURRENT_TIMESTAMP()),
# MAGIC   (2013, 1012, 'paypal',          34.00, 'success', '2023-08-25', CURRENT_TIMESTAMP()),
# MAGIC   (2014, 1013, 'bank_transfer', 250.00, 'success', '2023-08-27', CURRENT_TIMESTAMP()),
# MAGIC   (2015, 1014, 'credit_card',    75.00, 'success', '2023-08-29', CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify all tables loaded with _loaded_at populated
# MAGIC SELECT 'raw_customers'  AS tbl, COUNT(*) AS rows, MAX(_loaded_at) AS last_loaded FROM enablement.ecommerce.raw_customers
# MAGIC UNION ALL
# MAGIC SELECT 'raw_orders',          COUNT(*), MAX(_loaded_at) FROM enablement.ecommerce.raw_orders
# MAGIC UNION ALL
# MAGIC SELECT 'raw_order_items',     COUNT(*), MAX(_loaded_at) FROM enablement.ecommerce.raw_order_items
# MAGIC UNION ALL
# MAGIC SELECT 'raw_products',        COUNT(*), MAX(_loaded_at) FROM enablement.ecommerce.raw_products
# MAGIC UNION ALL
# MAGIC SELECT 'raw_payments',        COUNT(*), MAX(_loaded_at) FROM enablement.ecommerce.raw_payments;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup complete!
# MAGIC
# MAGIC Next steps:
# MAGIC 1. Run `01_lakeflow_pipeline.py` to create the DLT medallion pipeline (13 tables)
# MAGIC 2. Run `02_metric_views.sql` in SQL Editor to create Databricks Metric Views
# MAGIC 3. Import `03_data_generator.py` and schedule it as a Databricks Workflow (30-min trigger)
# MAGIC    — keeps raw_customers, raw_orders, and raw_order_items fresh
# MAGIC    — raw_payments is deliberately excluded to simulate a stale payment feed
# MAGIC 4. Run `dbt build` from `platform/` to build all mart tables
# MAGIC 5. After 2+ days without running the demo setup again, run `dbt source freshness`
# MAGIC    to see raw_payments flagged as stale while all other sources remain fresh
