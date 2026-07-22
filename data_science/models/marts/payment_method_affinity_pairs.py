"""
Payment-method co-usage affinity.

Identifies which payment methods are frequently used by the same customers,
with average spend per method. Consumes the platform project's governed
fct_orders mart through dbt Mesh, so it uses the same order and payment
definitions as marketing and finance — single source of truth.

This model demonstrates a use case that is naturally Python-native: self-join
pair generation is awkward in SQL but concise in PySpark. dbt Python models let
the DS team use the right tool for the job while still participating in the
governed dbt DAG.

Note: true *product* co-purchase affinity needs order-item grain, which this
demo does not expose as a public Mesh mart (fct_orders is order grain). Payment
method is the co-occurrence signal available from the governed marts.
"""


def model(dbt, session):
    from pyspark.sql import functions as F

    # Cross-project ref — validated at compile time by dbt Mesh.
    orders = dbt.ref("platform", "fct_orders")

    # One row per (customer, payment_method) usage, completed orders only.
    customer_methods = (
        orders
        .select("customer_id", "payment_method", "amount_paid")
        .filter(F.col("status") == "completed")
    )

    # Self-join on customer to build unordered payment-method pairs (a < b),
    # then count how many customers use both.
    method_pairs = (
        customer_methods.alias("a")
        .join(
            customer_methods.alias("b"),
            (F.col("a.customer_id") == F.col("b.customer_id"))
            & (F.col("a.payment_method") < F.col("b.payment_method")),
        )
        .groupBy(
            F.col("a.payment_method").alias("method_a"),
            F.col("b.payment_method").alias("method_b"),
        )
        .agg(
            F.countDistinct(F.col("a.customer_id")).alias("shared_customers"),
            F.round(F.avg(F.col("a.amount_paid")), 2).alias("avg_spend_method_a"),
            F.round(F.avg(F.col("b.amount_paid")), 2).alias("avg_spend_method_b"),
        )
        .orderBy(F.col("shared_customers").desc())
    )

    return method_pairs
