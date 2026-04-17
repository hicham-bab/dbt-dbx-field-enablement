# Databricks notebook source
# MAGIC %md
# MAGIC # E-Commerce Demo — Raw Data Setup
# MAGIC
# MAGIC Run this notebook once to create the `<your_catalog>.<your_schema>` catalog/schema
# MAGIC and load all raw Delta tables used by both the dbt platform project
# MAGIC and the Lakeflow pipeline demo.
# MAGIC
# MAGIC Each table includes a `_loaded_at` TIMESTAMP column so that
# MAGIC `dbt source freshness` can check how recently each source was updated.
# MAGIC
# MAGIC **Date range:** Orders span October 2024 → March 2026.
# MAGIC "Last month" (February 2026) and year-over-year (2025 vs 2026) queries return real data.
# MAGIC
# MAGIC **Expected row counts after setup:**
# MAGIC | Table | Rows |
# MAGIC |---|---|
# MAGIC | raw_customers | 20 |
# MAGIC | raw_orders | 71 |
# MAGIC | raw_order_items | 76 |
# MAGIC | raw_products | 15 |
# MAGIC | raw_payments | 71 |
# MAGIC | raw_reviews | 35 |
# MAGIC
# MAGIC **Source freshness design:**
# MAGIC | Table | Updated by generator? | Freshness threshold |
# MAGIC |---|---|---|
# MAGIC | raw_customers | Yes (30 min schedule) | error after 6 hours |
# MAGIC | raw_orders | Yes (30 min schedule) | error after 6 hours |
# MAGIC | raw_order_items | Yes (30 min schedule) | error after 6 hours |
# MAGIC | raw_products | No (static catalog) | error after 7 days |
# MAGIC | raw_payments | **No — simulates stale payment feed** | **error after 2 days** |
# MAGIC | raw_reviews | No (static for demo) | error after 7 days |

# COMMAND ----------

# -- Configure your namespace here to avoid collisions with other users --
dbutils.widgets.text("catalog", "enablement", "Catalog Name")
dbutils.widgets.text("schema", "ecommerce", "Schema Name")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS ${catalog};
# MAGIC USE CATALOG ${catalog};
# MAGIC CREATE SCHEMA IF NOT EXISTS ${schema};
# MAGIC USE SCHEMA ${schema};

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ${catalog}.${schema}.raw_customers (
# MAGIC   customer_id   INT,
# MAGIC   first_name    STRING,
# MAGIC   last_name     STRING,
# MAGIC   email         STRING,
# MAGIC   created_at    DATE,
# MAGIC   country       STRING,
# MAGIC   _loaded_at    TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO ${catalog}.${schema}.raw_customers VALUES
# MAGIC   -- Original cohort: joined 2023–2024
# MAGIC   (1,  'Alice',  'Martin',  'alice.martin@example.com',  '2023-01-15', 'US', CURRENT_TIMESTAMP()),
# MAGIC   (2,  'Bob',    'Chen',    'bob.chen@example.com',      '2023-02-20', 'CA', CURRENT_TIMESTAMP()),
# MAGIC   (3,  'Clara',  'Nguyen',  'clara.nguyen@example.com',  '2023-03-05', 'US', CURRENT_TIMESTAMP()),
# MAGIC   (4,  'David',  'Osei',    'david.osei@example.com',    '2023-03-18', 'GB', CURRENT_TIMESTAMP()),
# MAGIC   (5,  'Eva',    'Rossi',   'eva.rossi@example.com',     '2023-04-01', 'IT', CURRENT_TIMESTAMP()),
# MAGIC   (6,  'Frank',  'Mueller', 'frank.mueller@example.com', '2023-04-22', 'DE', CURRENT_TIMESTAMP()),
# MAGIC   (7,  'Grace',  'Kim',     'grace.kim@example.com',     '2023-05-10', 'KR', CURRENT_TIMESTAMP()),
# MAGIC   (8,  'Hugo',   'Silva',   'hugo.silva@example.com',    '2023-06-03', 'BR', CURRENT_TIMESTAMP()),
# MAGIC   (9,  'Iris',   'Dubois',  'iris.dubois@example.com',   '2023-06-28', 'FR', CURRENT_TIMESTAMP()),
# MAGIC   (10, 'James',  'Patel',   'james.patel@example.com',   '2023-07-14', 'IN', CURRENT_TIMESTAMP()),
# MAGIC   -- Growth cohort: joined 2024–2025
# MAGIC   (11, 'Lena',   'Kovac',   'lena.kovac@example.com',    '2024-08-20', 'DE', CURRENT_TIMESTAMP()),
# MAGIC   (12, 'Omar',   'Adeyemi', 'omar.adeyemi@example.com',  '2024-09-05', 'GB', CURRENT_TIMESTAMP()),
# MAGIC   (13, 'Priya',  'Sharma',  'priya.sharma@example.com',  '2024-10-12', 'IN', CURRENT_TIMESTAMP()),
# MAGIC   (14, 'Lucas',  'Becker',  'lucas.becker@example.com',  '2024-11-03', 'DE', CURRENT_TIMESTAMP()),
# MAGIC   (15, 'Mei',    'Zhang',   'mei.zhang@example.com',     '2024-11-28', 'JP', CURRENT_TIMESTAMP()),
# MAGIC   (16, 'Tariq',  'Hassan',  'tariq.hassan@example.com',  '2024-12-15', 'FR', CURRENT_TIMESTAMP()),
# MAGIC   (17, 'Sofia',  'Reyes',   'sofia.reyes@example.com',   '2025-01-08', 'MX', CURRENT_TIMESTAMP()),
# MAGIC   (18, 'Aiden',  'Novak',   'aiden.novak@example.com',   '2025-02-14', 'CA', CURRENT_TIMESTAMP()),
# MAGIC   (19, 'Yuki',   'Tanaka',  'yuki.tanaka@example.com',   '2025-03-22', 'JP', CURRENT_TIMESTAMP()),
# MAGIC   (20, 'Carlos', 'Mendez',  'carlos.mendez@example.com', '2025-05-10', 'MX', CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ${catalog}.${schema}.raw_products (
# MAGIC   product_id   INT,
# MAGIC   product_name STRING,
# MAGIC   category     STRING,
# MAGIC   unit_price   DECIMAL(10,2),
# MAGIC   is_active    BOOLEAN,
# MAGIC   _loaded_at   TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO ${catalog}.${schema}.raw_products VALUES
# MAGIC   -- Original catalog
# MAGIC   (101, 'Classic T-Shirt',            'apparel',     35.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (102, 'Running Shoes',               'footwear',    45.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (103, 'Wireless Earbuds',            'electronics', 29.99,  true, CURRENT_TIMESTAMP()),
# MAGIC   (104, 'Yoga Mat',                    'fitness',     80.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (105, 'Protein Powder',              'nutrition',  150.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (106, 'Denim Jacket',                'apparel',     54.99,  true, CURRENT_TIMESTAMP()),
# MAGIC   (107, 'Cycling Gloves',              'fitness',     90.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (108, 'Smart Watch',                 'electronics', 320.00, true, CURRENT_TIMESTAMP()),
# MAGIC   (109, 'Noise Cancelling Headphones', 'electronics', 250.00, true, CURRENT_TIMESTAMP()),
# MAGIC   (110, 'Trail Running Shoes',         'footwear',   145.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   -- Expanded catalog (added 2025)
# MAGIC   (111, 'Resistance Bands',            'fitness',     25.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (112, 'Whey Protein Bar',            'nutrition',   35.00,  true, CURRENT_TIMESTAMP()),
# MAGIC   (113, 'Polo Shirt',                  'apparel',     49.99,  true, CURRENT_TIMESTAMP()),
# MAGIC   (114, 'Bluetooth Speaker',           'electronics', 89.99,  true, CURRENT_TIMESTAMP()),
# MAGIC   (115, 'Basketball Shoes',            'footwear',   110.00,  true, CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ${catalog}.${schema}.raw_orders (
# MAGIC   order_id       INT,
# MAGIC   customer_id    INT,
# MAGIC   order_date     DATE,
# MAGIC   status         STRING,
# MAGIC   amount         DECIMAL(10,2),
# MAGIC   payment_method STRING,
# MAGIC   _loaded_at     TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO ${catalog}.${schema}.raw_orders VALUES
# MAGIC   -- Q4 2024 (Oct–Dec) — original seed data, dates shifted forward
# MAGIC   (1001,  1,  '2024-10-01', 'completed',  120.50, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1002,  2,  '2024-10-03', 'completed',   45.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1003,  3,  '2024-10-05', 'shipped',    310.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1004,  1,  '2024-10-07', 'completed',   89.99, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1005,  4,  '2024-10-10', 'returned',    55.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1006,  5,  '2024-10-12', 'completed',  670.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1007,  6,  '2024-10-14', 'placed',      29.99, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1008,  7,  '2024-10-15', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1009,  2,  '2024-11-18', 'completed',   88.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1010,  8,  '2024-11-20', 'shipped',    145.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1011,  3,  '2024-11-22', 'completed',  520.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1012,  9,  '2024-11-25', 'returned',    34.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1013, 10,  '2024-12-01', 'completed',  250.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1014,  1,  '2024-12-10', 'completed',   75.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1015,  5,  '2024-12-15', 'placed',     410.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   -- Q1 2025 (Jan–Mar)
# MAGIC   (1016,  3,  '2025-01-05', 'completed',  245.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1017,  7,  '2025-01-12', 'completed',   89.99, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1018,  1,  '2025-01-20', 'returned',    55.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1019,  5,  '2025-01-28', 'completed',  320.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1020,  9,  '2025-02-04', 'shipped',    145.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1021,  2,  '2025-02-10', 'completed',   67.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1022, 11,  '2025-02-14', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1023,  4,  '2025-02-20', 'returned',    34.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1024,  6,  '2025-03-03', 'completed',  520.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1025,  8,  '2025-03-15', 'completed',   75.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1026, 10,  '2025-03-28', 'completed',   88.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   -- Q2 2025 (Apr–Jun)
# MAGIC   (1027, 12,  '2025-04-05', 'completed',  340.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1028,  1,  '2025-04-18', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1029,  3,  '2025-05-02', 'completed',  670.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1030,  7,  '2025-05-16', 'completed',  120.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1031,  5,  '2025-05-28', 'returned',    29.99, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1032, 13,  '2025-06-04', 'completed',  450.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1033,  2,  '2025-06-18', 'completed',   89.99, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1034,  9,  '2025-06-27', 'shipped',    145.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   -- Q3 2025 (Jul–Sep)
# MAGIC   (1035,  4,  '2025-07-04', 'completed',  320.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1036, 14,  '2025-07-18', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1037,  6,  '2025-08-06', 'completed',  250.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1038, 11,  '2025-08-22', 'returned',   120.50, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1039,  1,  '2025-08-30', 'completed',  520.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1040,  8,  '2025-09-08', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1041, 15,  '2025-09-20', 'completed',   55.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1042, 16,  '2025-09-28', 'completed',  410.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   -- Q4 2025 (Oct–Dec)
# MAGIC   (1043,  2,  '2025-10-03', 'completed',  310.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1044, 12,  '2025-10-15', 'returned',    89.99, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1045,  5,  '2025-10-28', 'completed',  670.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1046,  1,  '2025-11-06', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1047, 17,  '2025-11-20', 'completed',  410.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1048,  3,  '2025-12-02', 'completed',  450.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1049,  9,  '2025-12-12', 'completed',  340.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1050,  7,  '2025-12-20', 'returned',    75.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1051,  6,  '2025-12-26', 'completed',  520.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1052, 14,  '2025-12-28', 'completed',  250.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   -- January 2026
# MAGIC   (1053,  4,  '2026-01-03', 'completed',  199.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1054, 18,  '2026-01-10', 'completed',   88.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1055,  2,  '2026-01-15', 'returned',    45.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1056,  5,  '2026-01-22', 'completed',  320.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1057, 10,  '2026-01-28', 'shipped',    145.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   -- February 2026 (last month — key for Genie demo)
# MAGIC   (1058,  1,  '2026-02-02', 'completed',  520.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1059, 13,  '2026-02-05', 'completed',   88.50, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1060,  7,  '2026-02-08', 'completed',  250.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1061, 19,  '2026-02-12', 'returned',    45.00, 'bank_transfer', CURRENT_TIMESTAMP()),
# MAGIC   (1062,  3,  '2026-02-14', 'completed',  670.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1063,  6,  '2026-02-18', 'completed',  199.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1064, 15,  '2026-02-22', 'completed',  340.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1065,  9,  '2026-02-26', 'completed',   89.99, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   -- March 2026 (current month — partial)
# MAGIC   (1066,  5,  '2026-03-01', 'completed',  410.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1067, 20,  '2026-03-05', 'placed',     199.00, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1068,  8,  '2026-03-10', 'completed',  145.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1069, 16,  '2026-03-18', 'shipped',    250.00, 'credit_card',   CURRENT_TIMESTAMP()),
# MAGIC   (1070,  2,  '2026-03-22', 'completed',   89.99, 'paypal',        CURRENT_TIMESTAMP()),
# MAGIC   (1071, 17,  '2026-03-24', 'completed',  320.00, 'credit_card',   CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ${catalog}.${schema}.raw_order_items (
# MAGIC   order_item_id INT,
# MAGIC   order_id      INT,
# MAGIC   product_id    INT,
# MAGIC   quantity      INT,
# MAGIC   unit_price    DECIMAL(10,2),
# MAGIC   _loaded_at    TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO ${catalog}.${schema}.raw_order_items VALUES
# MAGIC   -- Original items (orders 1001–1013)
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
# MAGIC   (20, 1013, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   -- Q1 2025 items
# MAGIC   (21, 1016, 104, 2,  80.00, CURRENT_TIMESTAMP()),
# MAGIC   (22, 1017, 102, 2,  45.00, CURRENT_TIMESTAMP()),
# MAGIC   (23, 1018, 103, 1,  55.00, CURRENT_TIMESTAMP()),
# MAGIC   (24, 1019, 107, 2,  90.00, CURRENT_TIMESTAMP()),
# MAGIC   (25, 1020, 110, 1, 145.00, CURRENT_TIMESTAMP()),
# MAGIC   (26, 1021, 101, 2,  33.75, CURRENT_TIMESTAMP()),
# MAGIC   (27, 1022, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (28, 1023, 106, 1,  34.00, CURRENT_TIMESTAMP()),
# MAGIC   (29, 1024, 109, 2, 260.00, CURRENT_TIMESTAMP()),
# MAGIC   (30, 1025, 105, 1,  75.00, CURRENT_TIMESTAMP()),
# MAGIC   (31, 1026, 101, 2,  44.25, CURRENT_TIMESTAMP()),
# MAGIC   -- Q2 2025 items
# MAGIC   (32, 1027, 107, 2, 170.00, CURRENT_TIMESTAMP()),
# MAGIC   (33, 1028, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (34, 1029, 109, 2, 335.00, CURRENT_TIMESTAMP()),
# MAGIC   (35, 1030, 103, 1, 120.50, CURRENT_TIMESTAMP()),
# MAGIC   (36, 1031, 103, 1,  29.99, CURRENT_TIMESTAMP()),
# MAGIC   (37, 1032, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   (38, 1033, 102, 2,  44.99, CURRENT_TIMESTAMP()),
# MAGIC   (39, 1034, 110, 1, 145.00, CURRENT_TIMESTAMP()),
# MAGIC   -- Q3 2025 items
# MAGIC   (40, 1035, 107, 2, 160.00, CURRENT_TIMESTAMP()),
# MAGIC   (41, 1036, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (42, 1037, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   (43, 1038, 104, 1, 120.50, CURRENT_TIMESTAMP()),
# MAGIC   (44, 1039, 108, 1, 320.00, CURRENT_TIMESTAMP()),
# MAGIC   (45, 1040, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (46, 1041, 111, 2,  25.00, CURRENT_TIMESTAMP()),
# MAGIC   (47, 1042, 106, 2,  54.99, CURRENT_TIMESTAMP()),
# MAGIC   -- Q4 2025 items
# MAGIC   (48, 1043, 107, 2, 155.00, CURRENT_TIMESTAMP()),
# MAGIC   (49, 1044, 102, 2,  44.99, CURRENT_TIMESTAMP()),
# MAGIC   (50, 1045, 109, 2, 335.00, CURRENT_TIMESTAMP()),
# MAGIC   (51, 1046, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (52, 1047, 106, 2,  54.99, CURRENT_TIMESTAMP()),
# MAGIC   (53, 1048, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   (54, 1049, 107, 2, 170.00, CURRENT_TIMESTAMP()),
# MAGIC   (55, 1050, 101, 2,  37.50, CURRENT_TIMESTAMP()),
# MAGIC   (56, 1051, 108, 1, 320.00, CURRENT_TIMESTAMP()),
# MAGIC   (57, 1052, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   -- January 2026 items
# MAGIC   (58, 1053, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (59, 1054, 101, 2,  44.25, CURRENT_TIMESTAMP()),
# MAGIC   (60, 1055, 102, 1,  45.00, CURRENT_TIMESTAMP()),
# MAGIC   (61, 1056, 107, 2, 160.00, CURRENT_TIMESTAMP()),
# MAGIC   (62, 1057, 110, 1, 145.00, CURRENT_TIMESTAMP()),
# MAGIC   -- February 2026 items (last month)
# MAGIC   (63, 1058, 108, 1, 320.00, CURRENT_TIMESTAMP()),
# MAGIC   (64, 1059, 101, 2,  44.25, CURRENT_TIMESTAMP()),
# MAGIC   (65, 1060, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   (66, 1061, 102, 1,  45.00, CURRENT_TIMESTAMP()),
# MAGIC   (67, 1062, 109, 2, 335.00, CURRENT_TIMESTAMP()),
# MAGIC   (68, 1063, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (69, 1064, 107, 2, 170.00, CURRENT_TIMESTAMP()),
# MAGIC   (70, 1065, 102, 1,  89.99, CURRENT_TIMESTAMP()),
# MAGIC   -- March 2026 items (current month)
# MAGIC   (71, 1066, 106, 2,  54.99, CURRENT_TIMESTAMP()),
# MAGIC   (72, 1067, 108, 1, 199.00, CURRENT_TIMESTAMP()),
# MAGIC   (73, 1068, 110, 1, 145.00, CURRENT_TIMESTAMP()),
# MAGIC   (74, 1069, 109, 1, 250.00, CURRENT_TIMESTAMP()),
# MAGIC   (75, 1070, 101, 1,  89.99, CURRENT_TIMESTAMP()),
# MAGIC   (76, 1071, 107, 2, 160.00, CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE ${catalog}.${schema}.raw_payments (
# MAGIC   payment_id     INT,
# MAGIC   order_id       INT,
# MAGIC   payment_method STRING,
# MAGIC   amount         DECIMAL(10,2),
# MAGIC   status         STRING,
# MAGIC   payment_date   DATE,
# MAGIC   _loaded_at     TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC -- raw_payments: seeded once, NOT updated by the data generator.
# MAGIC -- Simulates a third-party payment processor feed that has gone silent.
# MAGIC -- dbt source freshness will warn after 1 day and error after 2 days.
# MAGIC INSERT INTO ${catalog}.${schema}.raw_payments VALUES
# MAGIC   -- Q4 2024 payments (aligned with shifted order dates)
# MAGIC   (2001, 1001, 'credit_card',   120.50, 'success', '2024-10-01', CURRENT_TIMESTAMP()),
# MAGIC   (2002, 1002, 'paypal',          45.00, 'success', '2024-10-03', CURRENT_TIMESTAMP()),
# MAGIC   (2003, 1003, 'credit_card',   310.00, 'success', '2024-10-05', CURRENT_TIMESTAMP()),
# MAGIC   (2004, 1004, 'credit_card',    89.99, 'success', '2024-10-07', CURRENT_TIMESTAMP()),
# MAGIC   (2005, 1005, 'bank_transfer',  55.00, 'success', '2024-10-10', CURRENT_TIMESTAMP()),
# MAGIC   (2006, 1005, 'bank_transfer',  55.00, 'failed',  '2024-10-11', CURRENT_TIMESTAMP()),
# MAGIC   (2007, 1006, 'credit_card',   670.00, 'success', '2024-10-12', CURRENT_TIMESTAMP()),
# MAGIC   (2008, 1007, 'paypal',         29.99, 'pending', '2024-10-14', CURRENT_TIMESTAMP()),
# MAGIC   (2009, 1008, 'credit_card',   199.00, 'success', '2024-10-15', CURRENT_TIMESTAMP()),
# MAGIC   (2010, 1009, 'paypal',         88.50, 'success', '2024-11-18', CURRENT_TIMESTAMP()),
# MAGIC   (2011, 1010, 'credit_card',   145.00, 'success', '2024-11-20', CURRENT_TIMESTAMP()),
# MAGIC   (2012, 1011, 'credit_card',   520.00, 'success', '2024-11-22', CURRENT_TIMESTAMP()),
# MAGIC   (2013, 1012, 'paypal',         34.00, 'success', '2024-11-25', CURRENT_TIMESTAMP()),
# MAGIC   (2014, 1013, 'bank_transfer', 250.00, 'success', '2024-12-01', CURRENT_TIMESTAMP()),
# MAGIC   (2015, 1014, 'credit_card',    75.00, 'success', '2024-12-10', CURRENT_TIMESTAMP()),
# MAGIC   -- Q1 2025 payments
# MAGIC   (2016, 1016, 'credit_card',   245.00, 'success', '2025-01-05', CURRENT_TIMESTAMP()),
# MAGIC   (2017, 1017, 'paypal',         89.99, 'success', '2025-01-12', CURRENT_TIMESTAMP()),
# MAGIC   (2018, 1018, 'bank_transfer',  55.00, 'success', '2025-01-20', CURRENT_TIMESTAMP()),
# MAGIC   (2019, 1019, 'credit_card',   320.00, 'success', '2025-01-28', CURRENT_TIMESTAMP()),
# MAGIC   (2020, 1020, 'credit_card',   145.00, 'success', '2025-02-04', CURRENT_TIMESTAMP()),
# MAGIC   (2021, 1021, 'paypal',         67.50, 'success', '2025-02-10', CURRENT_TIMESTAMP()),
# MAGIC   (2022, 1022, 'credit_card',   199.00, 'success', '2025-02-14', CURRENT_TIMESTAMP()),
# MAGIC   (2023, 1023, 'paypal',         34.00, 'success', '2025-02-20', CURRENT_TIMESTAMP()),
# MAGIC   (2024, 1024, 'credit_card',   520.00, 'success', '2025-03-03', CURRENT_TIMESTAMP()),
# MAGIC   (2025, 1025, 'bank_transfer',  75.00, 'success', '2025-03-15', CURRENT_TIMESTAMP()),
# MAGIC   (2026, 1026, 'paypal',         88.50, 'success', '2025-03-28', CURRENT_TIMESTAMP()),
# MAGIC   -- Q2 2025 payments
# MAGIC   (2027, 1027, 'credit_card',   340.00, 'success', '2025-04-05', CURRENT_TIMESTAMP()),
# MAGIC   (2028, 1028, 'credit_card',   199.00, 'success', '2025-04-18', CURRENT_TIMESTAMP()),
# MAGIC   (2029, 1029, 'credit_card',   670.00, 'success', '2025-05-02', CURRENT_TIMESTAMP()),
# MAGIC   (2030, 1030, 'paypal',        120.50, 'success', '2025-05-16', CURRENT_TIMESTAMP()),
# MAGIC   (2031, 1031, 'credit_card',    29.99, 'success', '2025-05-28', CURRENT_TIMESTAMP()),
# MAGIC   (2032, 1032, 'credit_card',   450.00, 'success', '2025-06-04', CURRENT_TIMESTAMP()),
# MAGIC   (2033, 1033, 'credit_card',    89.99, 'success', '2025-06-18', CURRENT_TIMESTAMP()),
# MAGIC   (2034, 1034, 'bank_transfer', 145.00, 'success', '2025-06-27', CURRENT_TIMESTAMP()),
# MAGIC   -- Q3 2025 payments
# MAGIC   (2035, 1035, 'credit_card',   320.00, 'success', '2025-07-04', CURRENT_TIMESTAMP()),
# MAGIC   (2036, 1036, 'credit_card',   199.00, 'success', '2025-07-18', CURRENT_TIMESTAMP()),
# MAGIC   (2037, 1037, 'paypal',        250.00, 'success', '2025-08-06', CURRENT_TIMESTAMP()),
# MAGIC   (2038, 1038, 'credit_card',   120.50, 'success', '2025-08-22', CURRENT_TIMESTAMP()),
# MAGIC   (2039, 1039, 'credit_card',   520.00, 'success', '2025-08-30', CURRENT_TIMESTAMP()),
# MAGIC   (2040, 1040, 'credit_card',   199.00, 'success', '2025-09-08', CURRENT_TIMESTAMP()),
# MAGIC   (2041, 1041, 'paypal',         55.00, 'success', '2025-09-20', CURRENT_TIMESTAMP()),
# MAGIC   (2042, 1042, 'credit_card',   410.00, 'success', '2025-09-28', CURRENT_TIMESTAMP()),
# MAGIC   -- Q4 2025 payments
# MAGIC   (2043, 1043, 'credit_card',   310.00, 'success', '2025-10-03', CURRENT_TIMESTAMP()),
# MAGIC   (2044, 1044, 'bank_transfer',  89.99, 'success', '2025-10-15', CURRENT_TIMESTAMP()),
# MAGIC   (2045, 1045, 'credit_card',   670.00, 'success', '2025-10-28', CURRENT_TIMESTAMP()),
# MAGIC   (2046, 1046, 'credit_card',   199.00, 'success', '2025-11-06', CURRENT_TIMESTAMP()),
# MAGIC   (2047, 1047, 'paypal',        410.00, 'success', '2025-11-20', CURRENT_TIMESTAMP()),
# MAGIC   (2048, 1048, 'credit_card',   450.00, 'success', '2025-12-02', CURRENT_TIMESTAMP()),
# MAGIC   (2049, 1049, 'credit_card',   340.00, 'success', '2025-12-12', CURRENT_TIMESTAMP()),
# MAGIC   (2050, 1050, 'credit_card',    75.00, 'success', '2025-12-20', CURRENT_TIMESTAMP()),
# MAGIC   (2051, 1051, 'credit_card',   520.00, 'success', '2025-12-26', CURRENT_TIMESTAMP()),
# MAGIC   (2052, 1052, 'bank_transfer', 250.00, 'success', '2025-12-28', CURRENT_TIMESTAMP()),
# MAGIC   -- January 2026 payments
# MAGIC   (2053, 1053, 'credit_card',   199.00, 'success', '2026-01-03', CURRENT_TIMESTAMP()),
# MAGIC   (2054, 1054, 'paypal',         88.50, 'success', '2026-01-10', CURRENT_TIMESTAMP()),
# MAGIC   (2055, 1055, 'bank_transfer',  45.00, 'success', '2026-01-15', CURRENT_TIMESTAMP()),
# MAGIC   (2056, 1056, 'credit_card',   320.00, 'success', '2026-01-22', CURRENT_TIMESTAMP()),
# MAGIC   (2057, 1057, 'credit_card',   145.00, 'success', '2026-01-28', CURRENT_TIMESTAMP()),
# MAGIC   -- February 2026 payments (last month — key for Genie demo)
# MAGIC   (2058, 1058, 'credit_card',   520.00, 'success', '2026-02-02', CURRENT_TIMESTAMP()),
# MAGIC   (2059, 1059, 'paypal',         88.50, 'success', '2026-02-05', CURRENT_TIMESTAMP()),
# MAGIC   (2060, 1060, 'credit_card',   250.00, 'success', '2026-02-08', CURRENT_TIMESTAMP()),
# MAGIC   (2061, 1061, 'bank_transfer',  45.00, 'success', '2026-02-12', CURRENT_TIMESTAMP()),
# MAGIC   (2062, 1062, 'credit_card',   670.00, 'success', '2026-02-14', CURRENT_TIMESTAMP()),
# MAGIC   (2063, 1063, 'paypal',        199.00, 'success', '2026-02-18', CURRENT_TIMESTAMP()),
# MAGIC   (2064, 1064, 'credit_card',   340.00, 'success', '2026-02-22', CURRENT_TIMESTAMP()),
# MAGIC   (2065, 1065, 'credit_card',    89.99, 'success', '2026-02-26', CURRENT_TIMESTAMP()),
# MAGIC   -- March 2026 payments (current month — partial)
# MAGIC   (2066, 1066, 'credit_card',   410.00, 'success', '2026-03-01', CURRENT_TIMESTAMP()),
# MAGIC   (2067, 1067, 'paypal',        199.00, 'pending', '2026-03-05', CURRENT_TIMESTAMP()),
# MAGIC   (2068, 1068, 'credit_card',   145.00, 'success', '2026-03-10', CURRENT_TIMESTAMP()),
# MAGIC   (2069, 1069, 'credit_card',   250.00, 'success', '2026-03-18', CURRENT_TIMESTAMP()),
# MAGIC   (2070, 1070, 'paypal',         89.99, 'success', '2026-03-22', CURRENT_TIMESTAMP()),
# MAGIC   (2071, 1071, 'credit_card',   320.00, 'success', '2026-03-24', CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC -- raw_reviews: customer product ratings, seeded once (static for demo).
# MAGIC -- Enables Genie to answer satisfaction questions: "Which products have the best reviews?"
# MAGIC -- rating scale: 1 (worst) to 5 (best)
# MAGIC CREATE OR REPLACE TABLE ${catalog}.${schema}.raw_reviews (
# MAGIC   review_id   INT,
# MAGIC   order_id    INT,
# MAGIC   product_id  INT,
# MAGIC   customer_id INT,
# MAGIC   rating      INT,
# MAGIC   review_date DATE,
# MAGIC   _loaded_at  TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC INSERT INTO ${catalog}.${schema}.raw_reviews VALUES
# MAGIC   -- Q4 2024 reviews
# MAGIC   (1,  1001, 101,  1, 4, '2024-10-05', CURRENT_TIMESTAMP()),
# MAGIC   (2,  1002, 102,  2, 5, '2024-10-07', CURRENT_TIMESTAMP()),
# MAGIC   (3,  1004, 101,  1, 3, '2024-10-12', CURRENT_TIMESTAMP()),
# MAGIC   (4,  1006, 107,  5, 5, '2024-10-18', CURRENT_TIMESTAMP()),
# MAGIC   (5,  1008, 109,  7, 4, '2024-10-20', CURRENT_TIMESTAMP()),
# MAGIC   (6,  1011, 107,  3, 5, '2024-11-30', CURRENT_TIMESTAMP()),
# MAGIC   (7,  1013, 109, 10, 4, '2024-12-08', CURRENT_TIMESTAMP()),
# MAGIC   (8,  1014, 101,  1, 5, '2024-12-15', CURRENT_TIMESTAMP()),
# MAGIC   -- Q1 2025 reviews
# MAGIC   (9,  1016, 104,  3, 4, '2025-01-10', CURRENT_TIMESTAMP()),
# MAGIC   (10, 1017, 102,  7, 5, '2025-01-18', CURRENT_TIMESTAMP()),
# MAGIC   (11, 1019, 107,  5, 3, '2025-02-02', CURRENT_TIMESTAMP()),
# MAGIC   (12, 1022, 108, 11, 5, '2025-02-20', CURRENT_TIMESTAMP()),
# MAGIC   (13, 1024, 109,  6, 4, '2025-03-10', CURRENT_TIMESTAMP()),
# MAGIC   -- Q2 2025 reviews
# MAGIC   (14, 1027, 107, 12, 4, '2025-04-12', CURRENT_TIMESTAMP()),
# MAGIC   (15, 1028, 108,  1, 5, '2025-04-25', CURRENT_TIMESTAMP()),
# MAGIC   (16, 1029, 109,  3, 5, '2025-05-10', CURRENT_TIMESTAMP()),
# MAGIC   (17, 1032, 109, 13, 3, '2025-06-12', CURRENT_TIMESTAMP()),
# MAGIC   (18, 1033, 102,  2, 4, '2025-06-25', CURRENT_TIMESTAMP()),
# MAGIC   -- Q3 2025 reviews
# MAGIC   (19, 1035, 107,  4, 5, '2025-07-12', CURRENT_TIMESTAMP()),
# MAGIC   (20, 1036, 108, 14, 4, '2025-07-28', CURRENT_TIMESTAMP()),
# MAGIC   (21, 1037, 109,  6, 5, '2025-08-14', CURRENT_TIMESTAMP()),
# MAGIC   (22, 1039, 108,  1, 4, '2025-09-06', CURRENT_TIMESTAMP()),
# MAGIC   (23, 1040, 108,  8, 5, '2025-09-15', CURRENT_TIMESTAMP()),
# MAGIC   -- Q4 2025 reviews
# MAGIC   (24, 1042, 106, 16, 3, '2025-10-05', CURRENT_TIMESTAMP()),
# MAGIC   (25, 1043, 107,  2, 4, '2025-10-12', CURRENT_TIMESTAMP()),
# MAGIC   (26, 1045, 109,  5, 5, '2025-11-04', CURRENT_TIMESTAMP()),
# MAGIC   (27, 1046, 108,  1, 5, '2025-11-14', CURRENT_TIMESTAMP()),
# MAGIC   (28, 1048, 109,  3, 4, '2025-12-10', CURRENT_TIMESTAMP()),
# MAGIC   (29, 1049, 107,  9, 3, '2025-12-20', CURRENT_TIMESTAMP()),
# MAGIC   -- February 2026 reviews (last month)
# MAGIC   (30, 1058, 108,  1, 5, '2026-02-08', CURRENT_TIMESTAMP()),
# MAGIC   (31, 1059, 101, 13, 4, '2026-02-12', CURRENT_TIMESTAMP()),
# MAGIC   (32, 1060, 109,  7, 5, '2026-02-15', CURRENT_TIMESTAMP()),
# MAGIC   (33, 1062, 109,  3, 5, '2026-02-20', CURRENT_TIMESTAMP()),
# MAGIC   (34, 1063, 108,  6, 4, '2026-02-25', CURRENT_TIMESTAMP()),
# MAGIC   -- March 2026 reviews
# MAGIC   (35, 1066, 106,  5, 4, '2026-03-08', CURRENT_TIMESTAMP());

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Verify all tables loaded with _loaded_at populated
# MAGIC SELECT 'raw_customers'  AS tbl, COUNT(*) AS rows, MAX(_loaded_at) AS last_loaded FROM ${catalog}.${schema}.raw_customers
# MAGIC UNION ALL
# MAGIC SELECT 'raw_orders',          COUNT(*), MAX(_loaded_at) FROM ${catalog}.${schema}.raw_orders
# MAGIC UNION ALL
# MAGIC SELECT 'raw_order_items',     COUNT(*), MAX(_loaded_at) FROM ${catalog}.${schema}.raw_order_items
# MAGIC UNION ALL
# MAGIC SELECT 'raw_products',        COUNT(*), MAX(_loaded_at) FROM ${catalog}.${schema}.raw_products
# MAGIC UNION ALL
# MAGIC SELECT 'raw_payments',        COUNT(*), MAX(_loaded_at) FROM ${catalog}.${schema}.raw_payments
# MAGIC UNION ALL
# MAGIC SELECT 'raw_reviews',         COUNT(*), MAX(_loaded_at) FROM ${catalog}.${schema}.raw_reviews;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup complete!
# MAGIC
# MAGIC **Data summary:**
# MAGIC - 20 customers (joined 2023–2025)
# MAGIC - 15 products across 5 categories
# MAGIC - 71 orders spanning October 2024 → March 2026
# MAGIC - 76 order items
# MAGIC - 71 payments (seeded, not updated by generator — simulates stale payment feed)
# MAGIC - 35 product reviews (rating 1–5)
# MAGIC
# MAGIC **Key revenue figures for demo validation:**
# MAGIC - February 2026 (last month) completed revenue: $2,157.49
# MAGIC - January 2026 completed revenue: $607.50
# MAGIC - Q4 2025 completed revenue: $3,148.00
# MAGIC
# MAGIC **Next steps:**
# MAGIC 1. Run `01_lakeflow_pipeline.py` to create the DLT medallion pipeline
# MAGIC 2. Run `02_metric_views.sql` in SQL Editor to create Databricks Metric Views
# MAGIC 3. Import `03_data_generator.py` and schedule it as a Databricks Workflow (30-min trigger)
# MAGIC    — keeps raw_customers, raw_orders, and raw_order_items fresh
# MAGIC    — raw_payments is deliberately excluded to simulate a stale payment feed
# MAGIC 4. Run `dbt build` from `platform/` to build all mart tables
# MAGIC 5. After 2+ days without running the demo setup again, run `dbt source freshness`
# MAGIC    to see raw_payments flagged as stale while all other sources remain fresh
