# Genie Demo Queries — All 3 Spaces

Use this as your script for running Genie queries across all three spaces.
Run queries in the order shown. The contrast between spaces is the demo.

---

## Query Set 1: "What was total revenue last month?"

| Space | Expected behavior | Talking point |
|---|---|---|
| Raw (Act 1) | Picks `amount` from `raw_orders` OR `raw_payments` — ambiguous | "Which column? Which table? Genie guessed." |
| Lakeflow (Act 3) | Finds `daily_revenue` in `gold_fct_revenue` — better | "Better, but the definition lives in a Python notebook." |
| dbt (Act 4) | `SUM(amount_paid) WHERE status = 'completed'` | "Exact match to our semantic layer definition. Auditable." |

---

## Query Set 2: "Show me revenue by customer segment"

| Space | Expected behavior | Talking point |
|---|---|---|
| Raw (Act 1) | Error or wrong — no `customer_segment` in raw tables | "Business concepts don't exist in raw data." |
| Lakeflow (Act 3) | Works — `customer_segment` exists in gold | "Works because I wrote it manually. Not from code." |
| dbt (Act 4) | Works perfectly — tested values, documented column | "Tested with `accepted_values`. Can't be wrong." |

---

## Query Set 3: "Which customers are at risk of churning?"

| Space | Expected behavior | Talking point |
|---|---|---|
| Raw (Act 1) | Genie makes up a threshold | "30 days? 60? 90? Genie guessed." |
| Lakeflow (Act 3) | Genie computes recency — threshold still guessed | "The threshold isn't defined in Lakeflow metadata." |
| dbt (Act 4) | Uses `most_recent_order_date`, applies 90-day rule from instructions | "Definition is in our YAML. Same PR as the model." |

---

## Query Set 4: "What is our return rate?"

| Space | Expected behavior | Talking point |
|---|---|---|
| Raw (Act 1) | Computes something — denominator may be wrong | "Returned / what? All orders? Only completed?" |
| Lakeflow (Act 3) | Closer but still ambiguous | "No formal definition of the denominator." |
| dbt (Act 4) | Uses semantic layer `return_rate` metric definition | "Ratio metric: returned_orders / total_orders. Versioned." |

---

## Query Set 5: "Show me month-over-month revenue growth"

| Space | Expected behavior | Talking point |
|---|---|---|
| Raw (Act 1) | May fail or produce inconsistent results | "Which column is monthly revenue? Genie guesses." |
| Lakeflow (Act 3) | Works against `gold_fct_revenue.revenue_month` | "Better — but revenue definition still in Python." |
| dbt (Act 4) | Uses semantic layer time granularity — consistent | "MetricFlow handles the time grain. Same definition every time." |

---

## Query Set 6: "Which 3 products generate the most revenue?"

| Space | Expected behavior | Talking point |
|---|---|---|
| Raw (Act 1) | Requires joining 3 tables — may produce wrong results | "Revenue from raw_orders or raw_payments? Join to items how?" |
| Lakeflow (Act 3) | Better but no product-level revenue in gold layer | "Gold layer doesn't have product-level aggregation." |
| dbt (Act 4) | Uses `dim_products` + `fct_orders` — correct with tested FKs | "Foreign key contract validated. Join is guaranteed safe." |

---

## Governance Moment (Act 4 only)

After showing a revenue number in Act 4, say:

> "A stakeholder just got this number. They ask: how do I know this is right?
> Here's the answer."

Then show (in terminal or VS Code):
```bash
git log platform/models/semantic/_semantic_models.yml
```

> "Every change to the revenue definition is here. Who changed it. When.
> Which PR reviewed it. This is the audit trail. This is governance.
> This is what dbt adds that Lakeflow alone cannot."

---

## Recovery Queries (if demo breaks)

If Genie gives a wrong answer in Act 4:

1. **Show the definition**: Open `_semantic_models.yml` and point to the metric definition
2. **Run the SQL manually**: Paste the correct SQL in the SQL Editor
3. **Use the talking point**: "Even when the AI gets it wrong, we have a ground truth.
   The definition is in the YAML. The SQL is deterministic. We can always verify."

If Genie is down or slow:
- Switch to showing the Streamlit app (Tab 3: Metric Views vs dbt SL)
- Walk through the `_marts.yml` file and explain contract enforcement
- Show `git log` on the semantic models file as a governance demo
