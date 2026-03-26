# Databricks notebook source
# MAGIC %md
# MAGIC # E-Commerce Data Generator
# MAGIC
# MAGIC Scheduled via a Databricks Job to run every 30 minutes.
# MAGIC Appends realistic synthetic e-commerce events to keep three sources fresh:
# MAGIC
# MAGIC | Source | Updated | Freshness threshold |
# MAGIC |---|---|---|
# MAGIC | raw_customers | Yes — ~1 new customer per hour | error after 6 hours |
# MAGIC | raw_orders | Yes — 2–4 new orders per run | error after 6 hours |
# MAGIC | raw_order_items | Yes — 1–3 items per new order | error after 6 hours |
# MAGIC | raw_products | No — static catalog | error after 7 days |
# MAGIC | **raw_payments** | **No — intentionally excluded** | **error after 2 days** |
# MAGIC
# MAGIC After 2 days, `dbt source freshness` will flag `raw_payments` as stale.
# MAGIC This simulates a payment processor integration that has gone silent —
# MAGIC a real-world scenario where orders are coming in but payments aren't being recorded.
# MAGIC
# MAGIC ## How to schedule this notebook
# MAGIC
# MAGIC 1. Jobs & Pipelines → Create → Job
# MAGIC 2. Task type: Notebook
# MAGIC 3. Notebook path: this notebook
# MAGIC 4. Cluster: Serverless (or any existing cluster)
# MAGIC 5. Schedule: Every 30 minutes (cron: `0 */30 * * * ?` or use the UI scheduler)
# MAGIC 6. Click Create

# COMMAND ----------

import random
from datetime import date, timedelta
from pyspark.sql import Row
from pyspark.sql.functions import current_timestamp, lit
from pyspark.sql.types import (
    StructType, StructField,
    IntegerType, StringType, DecimalType, BooleanType, DateType, TimestampType
)
from decimal import Decimal

# ── Config ─────────────────────────────────────────────────────────────────────

CATALOG = "enablement"
SCHEMA  = "ecommerce"

# Number of new orders to insert per run (randomised for realism)
NEW_ORDERS_PER_RUN = random.randint(2, 4)

# ── Helpers ───────────────────────────────────────────────────────────────────

def tbl(name):
    return f"{CATALOG}.{SCHEMA}.{name}"

def max_id(table, col):
    """Returns the current maximum value of an integer ID column."""
    result = spark.sql(f"SELECT COALESCE(MAX({col}), 0) AS m FROM {tbl(table)}")
    return result.collect()[0]["m"]

def existing_customer_ids():
    return [r["customer_id"] for r in spark.sql(f"SELECT customer_id FROM {tbl('raw_customers')}").collect()]

def existing_product_ids():
    return [r["product_id"] for r in spark.sql(f"SELECT product_id FROM {tbl('raw_products')}").collect()]

# ── Realistic data pools ──────────────────────────────────────────────────────

FIRST_NAMES  = ["Lena", "Omar", "Priya", "Lucas", "Mei", "Tariq", "Sofia", "Aiden",
                "Yuki", "Carlos", "Nadia", "Finn", "Amara", "Theo", "Leila"]
LAST_NAMES   = ["Kovac", "Adeyemi", "Sharma", "Becker", "Zhang", "Hassan", "Reyes",
                "Novak", "Tanaka", "Mendez", "Okonkwo", "Walsh", "Diallo", "Park"]
COUNTRIES    = ["US", "CA", "GB", "DE", "FR", "IT", "ES", "NL", "AU", "JP", "KR", "BR", "IN", "MX"]
# Only 'placed' and 'shipped' — the order management system cannot mark orders 'completed'
# or 'returned' without a corresponding payment record. 'completed' is set by the payment
# processor (raw_payments), which is intentionally excluded from this generator to simulate
# a stale feed. Generating 'completed' without a payment causes assert_positive_revenue to fail.
STATUSES     = ["placed", "placed", "placed", "shipped", "shipped"]
PAY_METHODS  = ["credit_card", "credit_card", "credit_card", "paypal", "bank_transfer"]

# ── Step 1: Occasionally add a new customer (roughly 1 per hour) ──────────────

print("Step 1: Checking whether to add a new customer...")

# ~50% chance per run = ~1 new customer per hour on a 30-min schedule
if random.random() < 0.5:
    next_customer_id = max_id("raw_customers", "customer_id") + 1
    first = random.choice(FIRST_NAMES)
    last  = random.choice(LAST_NAMES)
    email = f"{first.lower()}.{last.lower()}{next_customer_id}@example.com"
    country = random.choice(COUNTRIES)
    today   = date.today()

    new_customer = spark.createDataFrame(
        [Row(
            customer_id = next_customer_id,
            first_name  = first,
            last_name   = last,
            email       = email,
            created_at  = today,
            country     = country,
        )],
        schema = StructType([
            StructField("customer_id", IntegerType()),
            StructField("first_name",  StringType()),
            StructField("last_name",   StringType()),
            StructField("email",       StringType()),
            StructField("created_at",  DateType()),
            StructField("country",     StringType()),
        ])
    ).withColumn("_loaded_at", current_timestamp())

    new_customer.write.mode("append").saveAsTable(tbl("raw_customers"))
    print(f"  Inserted customer {next_customer_id}: {first} {last} ({country})")
else:
    print("  No new customer this run.")

# ── Step 2: Insert new orders ─────────────────────────────────────────────────

print(f"\nStep 2: Inserting {NEW_ORDERS_PER_RUN} new orders...")

customer_ids = existing_customer_ids()
next_order_id = max_id("raw_orders", "order_id") + 1
new_order_ids = []

order_rows = []
for i in range(NEW_ORDERS_PER_RUN):
    oid    = next_order_id + i
    cid    = random.choice(customer_ids)
    status = random.choice(STATUSES)
    method = random.choice(PAY_METHODS)
    amount = Decimal(str(round(random.uniform(20.0, 600.0), 2)))
    odate  = date.today() - timedelta(days=random.randint(0, 2))

    order_rows.append(Row(
        order_id       = oid,
        customer_id    = cid,
        order_date     = odate,
        status         = status,
        amount         = amount,
        payment_method = method,
    ))
    new_order_ids.append(oid)
    print(f"  Order {oid}: customer={cid}, status={status}, amount=${amount}, method={method}")

orders_df = spark.createDataFrame(
    order_rows,
    schema = StructType([
        StructField("order_id",       IntegerType()),
        StructField("customer_id",    IntegerType()),
        StructField("order_date",     DateType()),
        StructField("status",         StringType()),
        StructField("amount",         DecimalType(10, 2)),
        StructField("payment_method", StringType()),
    ])
).withColumn("_loaded_at", current_timestamp())

orders_df.write.mode("append").saveAsTable(tbl("raw_orders"))
print(f"  Inserted {NEW_ORDERS_PER_RUN} orders.")

# ── Step 3: Insert order items for each new order ─────────────────────────────

print("\nStep 3: Inserting order items...")

product_ids = existing_product_ids()
next_item_id = max_id("raw_order_items", "order_item_id") + 1

item_rows = []
item_counter = 0
for oid in new_order_ids:
    n_items = random.randint(1, 3)
    chosen_products = random.sample(product_ids, min(n_items, len(product_ids)))
    for pid in chosen_products:
        qty        = random.randint(1, 3)
        unit_price = Decimal(str(round(random.uniform(15.0, 350.0), 2)))
        item_rows.append(Row(
            order_item_id = next_item_id + item_counter,
            order_id      = oid,
            product_id    = pid,
            quantity      = qty,
            unit_price    = unit_price,
        ))
        item_counter += 1

items_df = spark.createDataFrame(
    item_rows,
    schema = StructType([
        StructField("order_item_id", IntegerType()),
        StructField("order_id",      IntegerType()),
        StructField("product_id",    IntegerType()),
        StructField("quantity",      IntegerType()),
        StructField("unit_price",    DecimalType(10, 2)),
    ])
).withColumn("_loaded_at", current_timestamp())

items_df.write.mode("append").saveAsTable(tbl("raw_order_items"))
print(f"  Inserted {item_counter} order items across {len(new_order_ids)} orders.")

# ── Step 4: raw_payments — intentionally skipped ──────────────────────────────

print("\nStep 4: raw_payments — SKIPPED (intentional).")
print("  raw_payments simulates a third-party payment processor feed.")
print("  It is not updated by this generator.")
print("  dbt source freshness will flag it as WARN after 1 day, ERROR after 2 days.")
print("  This is the demo moment: orders are flowing in, but payments have gone silent.")

# ── Summary ───────────────────────────────────────────────────────────────────

print("\n=== Run complete ===")
summary = spark.sql(f"""
    SELECT 'raw_customers'  AS tbl, COUNT(*) AS total_rows, MAX(_loaded_at) AS last_loaded FROM {tbl('raw_customers')}
    UNION ALL
    SELECT 'raw_orders',          COUNT(*), MAX(_loaded_at) FROM {tbl('raw_orders')}
    UNION ALL
    SELECT 'raw_order_items',     COUNT(*), MAX(_loaded_at) FROM {tbl('raw_order_items')}
    UNION ALL
    SELECT 'raw_products',        COUNT(*), MAX(_loaded_at) FROM {tbl('raw_products')}
    UNION ALL
    SELECT 'raw_payments',        COUNT(*), MAX(_loaded_at) FROM {tbl('raw_payments')}
""")
display(summary)
