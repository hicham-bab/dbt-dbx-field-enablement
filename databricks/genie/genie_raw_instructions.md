# Genie Space: Raw Tables (Act 1 — The Problem)

## Purpose

This Genie Space is intentionally set up on raw, undocumented tables to show the
audience what Genie looks like **without** dbt's metadata layer. Use this in Act 1
of the demo to establish the problem before showing the solution.

---

## Tables to Add

When creating this Genie Space in Databricks:

1. AI/BI → Genie → Create Genie Space
2. Name: `E-Commerce (Raw — Act 1)`
3. Add these tables only:
   - `enablement.ecommerce.raw_customers`
   - `enablement.ecommerce.raw_orders`
   - `enablement.ecommerce.raw_order_items`
   - `enablement.ecommerce.raw_products`
   - `enablement.ecommerce.raw_payments`
   - `enablement.ecommerce.raw_reviews`

---

## Instructions (paste into Genie Space Instructions field)

```
This is raw e-commerce data. Orders span October 2024 to March 2026.

Tables:
- raw_customers: customer records
- raw_orders: order records
- raw_order_items: order line items
- raw_products: product catalog
- raw_payments: payment records
- raw_reviews: customer product ratings (1–5 scale)

Revenue is in the amount column of raw_orders or the amount column of raw_payments.
```

**Note:** Keep these instructions intentionally minimal. The goal is to show Genie
struggling with ambiguity — which column is revenue? Is it gross or net? What does
`status` mean? Let the audience see Genie make assumptions.

---

## Demo Script for Act 1

Ask these questions in sequence. Do NOT correct Genie's answers — let them stand.

1. **"What was total revenue last month?"**
   - Expected: Genie picks `amount` from either `raw_orders` or `raw_payments` — both exist, both plausible
   - Talking point: "Notice Genie had to guess which table and which column to use."

2. **"Show me revenue by customer segment"**
   - Expected: Genie may error (no segment column in raw tables) or return wrong results
   - Talking point: "There's no `customer_segment` column in raw data — Genie can't answer this."

3. **"How many high-value customers do we have?"**
   - Expected: Genie doesn't know what "high-value" means — no definition in these tables
   - Talking point: "Business concepts like 'high-value' don't exist in raw data. Genie has to guess."

4. **"What is our return rate?"**
   - Expected: Genie may count rows where status = 'returned' but may not divide correctly
   - Talking point: "Even a simple metric requires knowing what the denominator is."

---

## Key Talking Points

> "Every question Genie just answered required a guess. Guess which column is revenue.
> Guess what 'high-value' means. Guess what the denominator for return rate is.
> When a stakeholder gets a number and asks 'can I trust this?', the honest answer
> with raw tables is: maybe."

> "This is not a Genie problem. This is a metadata problem. Genie is only as good
> as the context you give it. Let me show you what happens when you give it better context."
