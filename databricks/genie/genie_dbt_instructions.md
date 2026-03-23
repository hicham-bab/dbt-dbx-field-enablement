# Genie Space: dbt Mart Tables + Semantic Layer (Act 4 — The Solution)

## Purpose

This Genie Space demonstrates the full dbt + Databricks integration: marts with
tested, documented columns, and a semantic layer with named metrics. Genie's answers
become accurate, consistent, and auditable.

---

## Prerequisites

- `dbt build` has completed successfully in the `platform/` project
- All tests are passing
- `persist_docs: relation: true, columns: true` is enabled in `dbt_project.yml`
- The following tables exist in `enablement.ecommerce`:
  - `dim_customers`, `dim_products`, `fct_orders`

---

## Tables to Add

1. AI/BI → Genie → Create Genie Space
2. Name: `E-Commerce Analytics (dbt + Semantic Layer — Act 4)`
3. Add these tables only:
   - `enablement.ecommerce.dim_customers`
   - `enablement.ecommerce.dim_products`
   - `enablement.ecommerce.fct_orders`
4. Connect to the dbt Semantic Layer (if configured) for metric query support

---

## Instructions (paste into Genie Space Instructions field)

These instructions are derived directly from `_marts.yml` and `_semantic_models.yml`.
The same source of truth used by dbt docs — no manual copy-paste required after initial setup.

```
This is a production e-commerce analytics database built with dbt on Databricks.
All tables have passed dbt data quality tests. Every column definition below comes
from version-controlled YAML reviewed in pull requests.

TABLES:

dim_customers — One row per customer. Primary key: customer_id.
  customer_id: unique identifier (integer). Primary key. Not null — tested.
  customer_segment: derived value tier — high_value (total LTV >= $500),
    mid_value ($100–$499), low_value (< $100). Tested with accepted_values.
    ONLY these three values exist in this column.
  total_lifetime_value: sum of all successful payment amounts (USD). Payments
    with status = 'success' only. NOT the same as order amount.
  number_of_orders: count of all orders placed, regardless of status.
  first_order_date / most_recent_order_date: date of first and latest order.
  country: uppercased two-letter ISO country code.

dim_products — One row per product. Primary key: product_id.
  category: lowercased product category.
    Values: apparel, electronics, fitness, footwear, nutrition.
  is_active: true if product is currently available for purchase.
  unit_price: current list price in USD.

fct_orders — One row per order. Primary key: order_id.
  status: placed | shipped | completed | returned — tested, only these 4 values exist.
  amount_paid: USD amount successfully paid (successful payments only).
    Tested: always >= 0.
  number_of_items: count of distinct line items in the order.
  payment_method: credit_card | paypal | bank_transfer.

BUSINESS RULES (version-controlled in dbt semantic layer — reviewed in PRs):
- Revenue = amount_paid WHERE status = 'completed'. Returned/placed/shipped orders
  are NOT counted as revenue. This is the canonical business definition.
- Customer lifetime value = SUM of payments WHERE payment status = 'success'.
- A "returning customer" = number_of_orders > 1.
- A "high-value customer" = total_lifetime_value >= 500.
- Return rate = COUNT(returned orders) / COUNT(all orders).
- "At risk" customer = most_recent_order_date more than 90 days ago.
- "Churned" customer = most_recent_order_date more than 180 days ago.

SEMANTIC LAYER METRICS (named, versioned definitions):
- total_recognised_revenue: SUM(amount_paid) WHERE status = 'completed'
- avg_order_value: AVG(amount_paid) for completed orders
- return_rate: COUNT(returned) / COUNT(all) * 100
- total_customers: COUNT DISTINCT customer_id
- avg_lifetime_value: AVG(total_lifetime_value)
- revenue_per_customer: total_recognised_revenue / total_customers
```

---

## Demo Script for Act 4

Ask the same questions as Acts 1 and 3 — highlight the accuracy, consistency, and auditability.

### Warm-up (establish baseline)
1. **"How many customers do we have?"**
   - Expected: Exact count using `COUNT(DISTINCT customer_id)` from `dim_customers`
   - Talking point: "This is now the exact same SQL dbt generates — no ambiguity."

2. **"Show me all high-value customers"**
   - Expected: `WHERE customer_segment = 'high_value'` — correct, tested values
   - Talking point: "Genie knows 'high_value' because it's in the column description AND
     tested with `accepted_values`. These are the only values that can exist here."

### Core demo
3. **"What was total revenue last month?"**
   - Expected: `SUM(amount_paid) WHERE status = 'completed'` from `fct_orders`
   - Talking point: "Revenue = completed orders only. This is our business definition.
     Genie read it from the Genie Space instructions which came from our `schema.yml`.
     The same YAML that's in Git. The same PR that was reviewed."

4. **"Show me revenue by customer segment"**
   - Expected: Join `dim_customers` + `fct_orders`, group by `customer_segment`
   - Talking point: "This works because both tables have tested, documented keys.
     The join is safe because `customer_id` is a foreign key constraint in the contract."

5. **"Which customers are at risk of churning?"**
   - Expected: Uses `most_recent_order_date`, applies the 90-day threshold from instructions
   - Talking point: "The definition of 'at risk' is in the instructions — which came from
     our `schema.yml`. Not from Genie's internal knowledge. From our version-controlled definition."

### Governance moment
6. **"How do I audit this revenue number?"**
   - Talking point (don't run in Genie — speak this):
     > "Open a terminal. Run: `git log platform/models/semantic/_semantic_models.yml`
     > You'll see every time the revenue definition changed, who changed it, and which
     > PR reviewed and approved the change. That's the audit trail."

### Complexity demo
7. **"What percentage of revenue comes from high-value customers?"**
   - Expected: Two-step calculation using segment + revenue — Genie can handle this with rich metadata
   - Talking point: "A complex question that requires joining two concepts. Works because
     both concepts are clearly defined in version-controlled YAML."

---

## Key Talking Points for Act 4

> "Three things happened that didn't happen in Act 1 or Act 3:
> 1. Every column has a tested, documented definition — not inferred from the column name
> 2. Business rules are explicit — not assumed by Genie's LLM
> 3. The audit trail is a git log — not 'trust me, the DLT notebook is correct'"

> "When a CFO asks 'how can I trust this number?', the answer is:
> pull request #47, reviewed by [name], approved on [date],
> definition: revenue = amount_paid where status = 'completed'.
> That's the answer dbt gives you."
