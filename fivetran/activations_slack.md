---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
---

# Activate: governed opportunity alerts → Slack (Fivetran Activations)

The back of the loop / the last mile. **Fivetran Activations** (reverse ETL, from the
Census acquisition) reads a **governed dbt mart** and pushes it to **Slack** - so the
sales team gets a real-time, trustworthy alert sourced from the same definitions Genie
and the dashboards use.

## What it activates

- **Source:** `crm_opportunity_alerts` - the governed dbt model
  (`platform/models/marts/crm/crm_opportunity_alerts.sql`) listing open opportunities
  that are high-value (>= $100k) or overdue. The alert logic is version-controlled,
  tested, and contract-backed - not an ad-hoc query.
- **Destination:** a Slack channel (e.g. `#sales-alerts`).
- **Trigger:** on new/changed rows each sync (an opportunity newly crossing the
  threshold triggers one message).

## Why Slack is a real win here

Databricks has **no first-class native reverse ETL**. "Alert the rep in Slack when a
big deal goes quiet" is a concrete business need with no native Databricks answer -
Fivetran Activations owns both ends of the movement, on the same platform as ingestion.

## Setup (UI)

1. **Connect the source** - the Databricks/Unity Catalog warehouse holding
   `enablement.ecommerce.crm_opportunity_alerts` (or your marts schema).
2. **Add the Slack destination** and authorize the workspace.
3. **Create an Activation (sync):**
   - Source model/table: `crm_opportunity_alerts`.
   - Sync key: `opportunity_id` (unique - drives new/changed detection).
   - Behavior: send a message on new/updated rows.
4. **Map fields to the Slack message.** Example template:

   ```
   :rotating_light: *{{ alert_reason | replace("_"," ") | title }}* - {{ opportunity_name }}
   Account: {{ account_name }}  |  Amount: ${{ amount }}  |  Close: {{ close_date }}
   Owner: {{ opportunity_owner }}  |  Stage: {{ stage_name }}
   ```
5. **Schedule** it (e.g. every 15 min) or run on completion of the dbt job.

## Representative config (Fivetran Activations / Census API shape)

```yaml
sync:
  name: "opportunity-alerts-to-slack"
  source:
    connection: databricks_uc
    model: crm_opportunity_alerts      # governed dbt mart
    primary_key: opportunity_id
  destination:
    connection: slack
    object: message
    channel: "#sales-alerts"
  behavior: send_on_new_or_updated
  field_mappings:
    - from: opportunity_name  to: text.title
    - from: account_name      to: text.account
    - from: amount            to: text.amount
    - from: close_date        to: text.close_date
    - from: opportunity_owner to: text.owner
    - from: alert_reason      to: text.reason
```

> Representative shape - confirm exact schema against the current Fivetran Activations
> API/UI. The durable design: activate a *governed dbt model* (not raw SQL) so the CRM
> alert, the Genie answer, and the dashboard all trace to one definition.

## The loop, closed

`crm_opportunity_alerts` is also queryable by **Genie** (it's a governed UC table with
persisted docs) and its inputs feed the pipeline **metrics** in the Semantic Layer. Same
governed source → Slack alert, Genie answer, and BI - no drift.
