# Genie Space: Salesforce CRM (Fivetran → dbt → Genie)

## Purpose

Demonstrates the Fivetran + dbt loop end-to-end: Salesforce data ingested by Fivetran
(MDLS → Unity Catalog), governed by dbt into contracted marts + a Semantic Layer, and
consumed by Genie. Genie answers pipeline questions from **governed definitions** - the
same ones that drive the Slack activation.

---

## Prerequisites

- Fivetran Salesforce connector + MDLS have landed `enablement.salesforce.*` in Unity
  Catalog (see `fivetran/mdls_salesforce_destination.md`).
- `dbt build --select staging.salesforce+ crm` has completed; tests pass.
- `persist_docs` is on (column docs land in Unity Catalog).
- Tables exist in `enablement.ecommerce`: `dim_accounts`, `fct_opportunities`,
  `crm_opportunity_alerts`.

---

## Tables to Add

1. AI/BI → Genie → Create Genie Space
2. Name: `Salesforce CRM (Fivetran + dbt)`
3. Add these tables only:
   - `enablement.ecommerce.dim_accounts`
   - `enablement.ecommerce.fct_opportunities`
   - `enablement.ecommerce.crm_opportunity_alerts`
4. Connect to the dbt Semantic Layer (if configured) so Genie can query the governed
   pipeline metrics by name.

---

## Instructions (paste into the Genie Space Instructions field)

These come directly from `platform/models/marts/crm/_crm.yml` - version-controlled,
PR-reviewed definitions, not hand-typed context.

```
This is a governed Salesforce CRM dataset: Fivetran ingested it, dbt tested and
contracted it. Every column definition is version-controlled YAML reviewed in a PR.

TABLES:

dim_accounts - one row per Salesforce account. Primary key: account_id.
  Key fields: account_name, account_type, industry, annual_revenue,
  number_of_employees, billing_country, account_owner.

fct_opportunities - one row per opportunity (deal). Primary key: opportunity_id.
  Foreign keys: account_id -> dim_accounts, owner_id.
  Key fields: stage_name, amount, close_date, probability, is_closed, is_won,
  opportunity_type, lead_source, opportunity_owner,
  weighted_amount (= amount x probability / 100).

crm_opportunity_alerts - open opportunities flagged as high-value (>= $100k) or
  overdue. This is the same governed list Fivetran Activations sends to Slack.

GOVERNED METRICS (prefer these over ad-hoc SQL):
  open_pipeline_amount     - SUM(amount) WHERE is_closed = false
  weighted_pipeline_amount - SUM(weighted_amount) WHERE is_closed = false
  won_amount               - SUM(amount) WHERE is_won = true
  avg_deal_size            - AVG(amount) WHERE is_won = true
  opportunity_count        - COUNT(DISTINCT opportunity_id)
  win_rate                 - won opportunities / closed opportunities (%)

RULES:
- "Pipeline" means OPEN opportunities (is_closed = false). Use open_pipeline_amount.
- "Bookings"/"won revenue" means is_won = true. Use won_amount.
- Win rate is won / closed, never won / all opportunities.
- Slice by stage_name, opportunity_type, lead_source, industry, or account_owner.
```

---

## Sample Questions

- "What's our open pipeline by stage?"
- "Win rate by lead source this quarter?"
- "Which accounts have the largest weighted pipeline?"
- "Show me the high-value or overdue open opportunities." (mirrors the Slack alert)

## Talking Points

- Genie's pipeline numbers match the Slack alerts and the BI dashboards because all
  three read the *same* governed dbt models - one definition, activated and analyzed
  everywhere.
- Ask "where does this number come from?" → trace `open_pipeline_amount` in Explorer to
  `fct_opportunities`, its contract, tests, and the Fivetran-landed Salesforce source.
