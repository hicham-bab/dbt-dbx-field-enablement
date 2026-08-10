---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
---

# Fivetran + dbt on Databricks - The Complete Governed Loop

Internal SA enablement. Since the **Fivetran + dbt Labs merger (completed
2026-06-01)**, one company now covers **ingestion → transformation → governance →
activation**. This doc gives SAs the confidence and the language to win the *data
layer* on Databricks accounts.

> **The stance:** Databricks is a great platform, and we run *on* it. But for the
> movement → governance → activation layer, **Fivetran + dbt beats the
> Databricks-native path on time-to-value and on the quality of the governed layer
> that Databricks AI (Genie, agents) consumes.** We win the data layer; we love the
> platform. Keep claims honest - like the rest of this repo, separate a *real gap*
> from *they just didn't configure it*, and confirm fast-moving competitive facts
> with PMM.

---

## The loop

```
   SaaS / DB / files                                            Operational tools
  (Salesforce, Stripe,                                        (Salesforce, HubSpot,
   Postgres, 700+)                                             Marketo, Ads, 200+)
        │                                                              ▲
        ▼                                                              │
 ┌──────────────┐   ┌───────────────────────┐   ┌───────────────┐   ┌──────────────┐
 │  Fivetran    │──▶│   Unity Catalog        │──▶│  dbt (Fusion) │──▶│  Fivetran    │
 │  ingest +    │   │  open tables           │   │  transform,   │   │  Activations │
 │  MDLS        │   │  (Delta + Iceberg)     │   │  contracts,   │   │  (reverse    │
 │              │   │                        │   │  Semantic     │   │  ETL)        │
 └──────────────┘   └───────────────────────┘   │  Layer, Mesh  │   └──────────────┘
                             │                   └───────┬───────┘
                             │                           │
                             └───────────────▶  Databricks AI  ◀──────┘
                                              (Genie, agents) consume
                                               the governed layer
```

**One-liner:** *"Databricks can do each step natively. Fivetran + dbt does the
movement → governance → activation layer with faster time-to-value and a
better-governed layer for AI - while running on Databricks."*

---

## Part 1: The four layers - where Fivetran + dbt wins

### 1. Ingestion

| | Databricks-native | Fivetran |
|---|---|---|
| What it is | Lakeflow Connect managed connectors (Salesforce, ServiceNow, SQL Server, Google Analytics, DB CDC, file sources) → Delta, UC-governed, serverless | 700+ mature managed connectors with automatic schema-drift handling and idempotent syncs |
| Where we win | Breadth and maturity of the connector catalog; long-tail SaaS/DB sources are turnkey day one; **faster time-to-value** - no pipeline to hand-build | |

**Honest note:** Lakeflow Connect is genuinely good and improving, and for a source
it already covers with streaming/Spark-native needs it can be the right call. The
win is breadth, schema-evolution maturity, and TTV on the long tail - *not* "Lakeflow
can't ingest." Position **complementary**: Fivetran for SaaS/long-tail + managed open
tables, Lakeflow for streaming/Spark-native. Both land governed tables in Unity
Catalog; dbt transforms either way.

### 2. Managed open tables (the Managed Data Lake Service)

| | Databricks-native | Fivetran MDLS |
|---|---|---|
| Table format | Delta-centric (UC now also supports managed Iceberg / an Iceberg REST catalog) | Writes **Delta AND Iceberg simultaneously** (Parquet + dual metadata) |
| Maintenance | Managed tables + Predictive Optimization (on Databricks compute) | Fivetran-managed compaction/optimization/retention - **no Databricks compute needed** |
| Catalog | Unity Catalog | Lands in **Unity Catalog** (BYO), or Polaris (default), Glue, BigQuery Metastore, OneLake |
| Where we win | Open, multi-engine, no single-vendor lock-in; managed maintenance off Databricks compute; the standout for **Iceberg-first / open-format customers** | |

This is the layer to lead with when a customer already has (or wants) an **Iceberg**
lakehouse - see Part 2.

### 3. Transform + govern

This is the existing strength of this repo. dbt (Fusion) on Databricks gives you
version-controlled SQL, contracts, tests, the Semantic Layer, metric views
(`materialized='metric_view'`), and Mesh - none of which native notebooks or
Lakeflow declarative pipelines provide. Full detail in `PLATFORM_COMPARISON.md`,
`METRIC_VIEWS_COMPARISON.md`, and `BATTLE_CARD.md`.

### 4. Activation (reverse ETL)

| | Databricks-native | Fivetran Activations |
|---|---|---|
| Reverse ETL | No first-class native reverse ETL product | **Fivetran Activations** (from the Census acquisition): sync governed marts/metrics from Databricks → Salesforce, HubSpot, Marketo, Ads, 200+ destinations |
| Where we win | This is a **clean gap**. The governed data has to reach the tools the business actually works in - Fivetran closes the loop | |

See Part 3.

---

## Part 2: The Iceberg angle (lead with this for open-format customers)

If a customer's data is (or is going) **Apache Iceberg**, MDLS is the strongest
opening:

- MDLS writes **both Iceberg and Delta metadata** over the same Parquet, so the
  customer isn't forced to pick a format and isn't locked to one engine - Databricks
  SQL/Spark, plus Trino, Snowflake, Flink, etc., can all read it.
- Fivetran **manages the table maintenance** (compaction, snapshots, retention)
  without consuming Databricks compute.
- It registers in **Unity Catalog** for governance, so it's a first-class citizen on
  the lakehouse - and dbt transforms it exactly like any other UC table.

**Talk track:** "You want an open Iceberg lakehouse and you want it governed in Unity
Catalog. MDLS lands your sources as managed Iceberg *and* Delta tables in UC, and
Fivetran maintains them for you - so you get an open, multi-engine lake with
warehouse-like ease, and dbt turns it into governed marts on top."

*(Verify current UC managed-Iceberg / Iceberg REST support with PMM - Databricks is
moving here; the durable win is dual-format + managed maintenance + turnkey-from-source.)*

---

## Part 3: Activation - the last mile that closes the loop

Governance is only valuable if the trusted data reaches where decisions happen.
**Fivetran Activations** (reverse ETL) pushes the governed dbt outputs back to
operational tools:

- Sync `mart_customer_segments` (or the RFM/churn features from the `data_science`
  project) to **Salesforce / HubSpot** so sales and marketing act on the *same*
  governed definitions the CFO sees in Genie.
- Because the definitions come from dbt (tested, contracted, PR-reviewed), the
  numbers in Salesforce match the numbers in Genie match the numbers in the
  dashboard - one governed source, activated everywhere.
- Usage-based (Monthly Active Rows), same platform as ingestion - no separate
  reverse-ETL vendor to buy and wire up.

**Why it wins:** Databricks has no first-class reverse ETL. "Getting governed data
into the CRM" is a real customer need with no native answer - Fivetran owns both ends
of the movement.

---

## Part 4: The governed layer for Databricks AI

This is the through-line that ties the loop to the customer's AI ambitions (and to
the Summit 2026 / Genie Ontology content in `FAQ.md` and `BATTLE_CARD.md`):

- Databricks' **Genie Ontology** is a *context layer* that *consumes* a semantic
  layer; Unity Catalog Metrics/Glossary feed it.
- **dbt** is the governed, version-controlled, multi-platform source of those
  definitions - it authors UC metric views, serves the Semantic Layer to every tool,
  and (with the merger's open **Agents Schema** standard) exposes semantic
  models/metrics/lineage/docs as SQL tables agents can read.
- So the *better-governed layer* Fivetran + dbt produces directly makes **Databricks
  AI more trustworthy**. The pitch isn't "instead of Genie" - it's "Genie and your
  agents are only as good as the governed context underneath, and that's what we
  build."

---

## Part 5: When Fivetran + dbt clearly wins (cheat sheet)

- **Iceberg / open-format** customer, or one who wants no format/engine lock-in.
- **SaaS-heavy or long-tail sources** (Salesforce, Stripe, NetSuite, Zendesk, …) -
  connector breadth + schema drift handling.
- **Time-to-value pressure** - turnkey ingest + managed tables + governed transform
  in one platform, vs assembling Lakeflow + notebooks + a reverse-ETL vendor.
- **Activation need** - governed data must reach CRM/marketing tools (no native
  Databricks reverse ETL).
- **AI/agent ambitions** - they need a governed context layer feeding Genie/agents.
- **Migrating off legacy ETL** (Informatica/Talend/Matillion) - see
  `MIGRATION_ACCELERATION.md`.

## Part 6: Where Databricks-native may suffice (be honest)

- Pure **streaming / Spark-native** ingestion already well-served by Lakeflow.
- A source **Lakeflow Connect already covers**, Delta-only shop, no multi-engine need.
- **Databricks-only** consumption, no operational-tool activation, few simple metrics.

Leading with a fair read of these builds credibility - then pivot to the layers where
we win.

---

## Part 7: Time to value - the summary argument

The combined platform compresses "raw source → governed, activated data" because it's
**one managed motion** instead of an assembly project:

| Step | Databricks-native path | Fivetran + dbt on Databricks |
|---|---|---|
| Ingest a SaaS/DB source | Build/enable a pipeline (or wait for a connector) | Turnkey connector, minutes |
| Land governed open tables | Delta managed tables; Iceberg maturing | MDLS: Delta + Iceberg in UC, managed |
| Transform + govern | Notebooks / Lakeflow declarative | dbt: contracts, tests, Semantic Layer, Mesh |
| Feed Genie/agents trustworthy context | Hand-curate UC metadata | Governed dbt definitions + metric views + Agents Schema |
| Activate to operational tools | No native reverse ETL | Fivetran Activations |
| **First governed, activated output** | Weeks, multi-tool assembly | **Days, one platform** |

---

## Worked example in this repo - Salesforce → dbt → Slack + Genie

This repo now ships a **runnable full-loop example** you can point at (not just prose):

| Stage | Where it lives |
|---|---|
| **Ingest** - Salesforce via MDLS → Unity Catalog | `fivetran/mdls_salesforce_destination.md` |
| **Source** - Fivetran Salesforce schema, freshness | `platform/models/staging/salesforce/_salesforce__sources.yml` |
| **Transform** - staging → governed marts | `platform/models/staging/salesforce/`, `platform/models/marts/crm/` (`dim_accounts`, `fct_opportunities`, `crm_opportunity_alerts`) |
| **Govern** - contracts + tests + Semantic Layer metrics | `platform/models/marts/crm/_crm.yml` (open_pipeline, win_rate, avg_deal_size, …) |
| **Activate** - governed alerts → Slack | `fivetran/activations_slack.md` (reverse-ETL `crm_opportunity_alerts`) |
| **Consume** - Genie on the governed CRM | `databricks/genie/genie_salesforce_crm_instructions.md` |

The point it proves: the *same* governed model (`crm_opportunity_alerts`, and the
pipeline metrics) drives the **Slack alert**, the **Genie answer**, and **BI** - one
definition, activated and analyzed everywhere, with no drift. It's built as a
self-contained CRM slice alongside the e-commerce demo, so both run independently.

> Adapting to a real account: swap the connector, then let the Fivetran ERD (or the
> `fivetran/dbt_salesforce_source` package) tell you the exact landed columns, and
> adjust the staging models. Salesforce custom fields (`*__c`) differ per org - verify
> the schema before relying on specific columns.

---

## Demo flow

See `DEMO_SCRIPT.md` - the optional **Act 0** (Fivetran MDLS ingest of Salesforce →
governed Iceberg/Delta in Unity Catalog) and the **final activation act** (reverse-ETL
`crm_opportunity_alerts` to **Slack**) bookend the existing 5-act dbt-on-Databricks
demo, turning it into the complete loop.

---

*Competitive claims here reflect capabilities as of mid-2026; Databricks is investing
across ingestion, open-table management, and AI context. Confirm specifics
(Lakeflow Connect coverage, UC managed Iceberg, any new reverse-ETL) with PMM before
leaning on them in a deal.*
