# Fivetran config — the ingest and activate ends of the loop

This directory holds the **Fivetran** configuration for the full-loop example:

```
Salesforce ──(connector + MDLS)──▶ Unity Catalog ──▶ dbt (platform/) ──▶ Genie
                                                          │
                                                          └─▶ Fivetran Activations ──▶ Slack
```

- **`mdls_salesforce_destination.md`** — the *ingest* end: a Salesforce connector
  writing through the **Managed Data Lake Service** into Unity Catalog as governed
  open Delta/Iceberg tables (the `salesforce` schema the dbt sources read).
- **`activations_slack.md`** — the *activate* end: **Fivetran Activations** (reverse
  ETL) syncing the governed `crm_opportunity_alerts` mart to a **Slack** channel.

The dbt transform in between lives in `platform/models/` (Salesforce staging →
`dim_accounts` / `fct_opportunities` marts + Semantic Layer). See
`FIVETRAN_DBT_DATABRICKS.md` for the narrative and `DEMO_SCRIPT.md` Acts 0 and 4h
for the live demo flow.

> These files are **representative configuration** (Fivetran is configured in its UI
> or via the Fivetran Terraform provider / REST API — there is no repo-native config
> file it reads). Use them as a working reference; confirm exact field names and the
> current UI against Fivetran's docs. Custom Salesforce fields vary per org — verify
> the connector schema before relying on specific columns.
