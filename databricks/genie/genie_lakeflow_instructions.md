# Genie Space: Lakeflow Gold Tables (Act 3 — Better But Still Ambiguous)

## Purpose

This Genie Space sits on the Lakeflow gold layer — cleaner than raw, but still
lacking column-level documentation. Use this in Act 3 to show that Lakeflow alone
doesn't fully solve the Genie quality problem.

---

## Prerequisites

The Lakeflow pipeline must have run successfully:
- `enablement.ecommerce_lakeflow.gold_dim_customers` exists
- `enablement.ecommerce_lakeflow.gold_fct_orders` exists
- `enablement.ecommerce_lakeflow.gold_fct_revenue` exists

---

## Tables to Add

1. AI/BI → Genie → Create Genie Space
2. Name: `E-Commerce (Lakeflow Gold — Act 3)`
3. Add these tables only:
   - `enablement.ecommerce_lakeflow.gold_dim_customers`
   - `enablement.ecommerce_lakeflow.gold_fct_orders`
   - `enablement.ecommerce_lakeflow.gold_fct_revenue`

---

## Instructions (paste into Genie Space Instructions field)

```
E-commerce data from the Lakeflow gold layer.

Tables:
- gold_dim_customers: customers with lifetime value and segment.
  customer_segment values: high_value, mid_value, low_value.
  total_lifetime_value: sum of successful payments (USD).
- gold_fct_orders: orders with items and payment totals.
  status values: placed, shipped, completed, returned.
  amount_paid: USD amount paid for this order.
- gold_fct_revenue: daily revenue aggregates (completed orders only).
  daily_revenue: total revenue for the day.

Revenue = daily_revenue column in gold_fct_revenue (completed orders only).
High-value customer = total_lifetime_value >= 500.
```

**Note:** These instructions are written manually. They must be kept in sync with
the DLT pipeline code manually. There is no `schema.yml` to generate them from.

---

## Demo Script for Act 3

Ask the same questions as Act 1 — note the improvement but highlight remaining gaps.

1. **"What was total revenue last month?"**
   - Expected: Better — Genie finds `daily_revenue` in `gold_fct_revenue`
   - Talking point: "Better. But `daily_revenue` is defined in Python code in the DLT notebook.
     The instruction I wrote manually says 'completed orders only' — but I had to write that.
     If the pipeline changes, I need to remember to update these instructions too."

2. **"Show me revenue by customer segment"**
   - Expected: Works — `customer_segment` exists with documented values
   - Talking point: "This works because I manually documented the segment values in the instructions.
     In the dbt version, this comes automatically from `schema.yml`."

3. **"Which customers are at risk of churning?"**
   - Expected: Genie makes up a recency threshold — no `days_since_last_order` column
   - Talking point: "Lakeflow gold doesn't have a recency column. Genie has to compute it,
     but there's no version-controlled definition of 'at risk'. In dbt, this is in the marketing
     Mesh project with an explicit `days_since_last_order` column and `marketing_segment` tested values."

4. **"What is our return rate?"**
   - Expected: Genie can compute it but may get the denominator wrong
   - Talking point: "The numerator and denominator for return rate are not defined.
     Compare this to the dbt semantic layer where `return_rate` is a named, versioned metric."

---

## Key Talking Points

> "Lakeflow gives us cleaner data — the medallion architecture works. But we're still
> writing instructions manually and keeping them in sync manually. The semantic layer
> is still us, writing text in a UI field, not code in a PR."

> "The real question is: when a stakeholder audits the number Genie gave them, what can
> they point to? With Lakeflow, they point to a DLT notebook. With dbt, they point to
> a YAML file with a Git history and a PR review. Let me show you Act 4."
