---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
---

# dbt + Databricks Field Enablement

A consolidated, demo-ready repo for dbt SAs and AEs enabling colleagues on
the dbt + Databricks joint story. Covers dbt Fusion, Genie + Semantic Layer,
dbt Mesh governance, and an honest Databricks metric views comparison.

> **Naming note (2026):** product names in this market moved three times in
> eighteen months. This repo uses **dbt platform** (formerly dbt Cloud), **Lakeflow
> pipelines** (formerly Delta Live Tables), **Declarative Automation Bundles**
> (formerly Databricks Asset Bundles), **Genie Agents** (formerly Genie spaces),
> **dbt Catalog** (formerly dbt Explorer) and **Studio IDE**. **dbt Wizard** and
> **dbt Copilot** are two different products, not one renamed.
>
> The rules are in **`NAMING.md`** and CI enforces them. Naming is still in
> transition; confirm anything customer-facing with PMM.

---

## What's in This Repo

| File / Directory | Purpose |
|---|---|
| `DEMO_SCRIPT.md` | 5-act, 20–25 min demo script with timing, talking points, Q&A anchors |
| `BATTLE_CARD.md` | **The call artifact.** One page, generated from `battlecard.yml` - do not edit directly |
| `docs/competitive_reference.md` | **The prep doc.** Long-form deep dives behind the card |
| `docs/ingestion_battle_card.md` | Lakeflow Connect vs Fivetran - the front half of the story, before raw tables exist |
| `docs/enablement_arc.md` | Build-native-first internal enablement: build twice, measure the delta |
| `METRIC_VIEWS_COMPARISON.md` | dbt Semantic Layer + Databricks metric views - complementary, and how dbt authors/governs them |
| `MIGRATION_ACCELERATION.md` | Legacy → dbt + Databricks migration: how dbt Wizard + Fusion create faster time to value |
| `FIVETRAN_DBT_DATABRICKS.md` | Fivetran + dbt on Databricks - the complete governed loop (ingest → govern → activate); competitive SA enablement |
| `FAQ.md` | Objection handling for customers, champions, and Databricks SAs |
| `SETUP.md` | Full environment setup - DBX workspace + dbt platform + Mesh |
| `platform/` | Producer dbt project (Fusion-conformant, contracts, semantic layer) |
| `marketing/` | Consumer dbt project - cross-project refs from platform |
| `finance/` | Consumer dbt project - cross-project refs from platform |
| `data_science/` | Consumer dbt project - Python models, DS features via Mesh |
| `databricks/notebooks/` | Setup + Lakeflow pipeline + Metric Views SQL + data generator + Mesh equivalent demo |
| `databricks/genie/` | Genie Agent configs + demo queries for all 3 acts |
| `databricks/app/` | Streamlit app (4 tabs) for the Databricks App deployment |
| `docs/` | Architecture diagrams, Mesh explainer, Fusion cheat sheet, DABs CI/CD guide |
| `databricks.yml` | Declarative Automation Bundle configuration (IaC for Databricks Jobs) |
| `resources/` | Bundle resource definitions (dbt job YAML) |
| `fivetran/` | Fivetran config for the full-loop example - MDLS (Salesforce → Unity Catalog) ingest + Activations (governed alerts → Slack) |
| `dbt_profiles/` | dbt profiles for Declarative Automation Bundle deployments (OAuth M2M) |
| `.github/workflows/` | CI/CD pipeline (GitHub Actions: validate -> deploy -> run) + docs lint and weekly source freshness |
| `NAMING.md` | Product naming rules (prose only, never code identifiers). Enforced by CI |
| `sources.yml` / `facts.yml` | Citation registry, and the demo's real numbers recomputed from the repo |
| `scripts/` | `naming_lint.py`, `build_citations.py`, `check_expiry.py`, `check_sources.py`, `check_facts.py`, `build_battlecard.py` |

---

## What the demo data actually contains

Quote these, not rounder-sounding numbers. They are computed from the seeded
`INSERT` statements in `databricks/notebooks/00_setup_raw_data.py` and verified by
`scripts/check_facts.py`:

| Fact | Value |
|---|---|
| dbt projects | **4** - `platform`, `marketing`, `finance` (core demo) + `data_science` (optional Act 4f) |
| Raw Delta tables | **6** |
| Platform models | **18** (9 staging, 2 intermediate, 6 marts incl. `crm/`, 1 metric view) |
| Contracted public marts | **3** - `dim_customers`, `dim_products`, `fct_orders` |
| Metric definitions | **23** - 15 on the e-commerce path (13 simple on the marts models + 1 ratio + 1 derived in `semantic/`) and 8 on the optional CRM path in `marts/crm/` |
| Tests on `fct_orders` | **7** |
| Orders | **71** (52 completed, 10 returned, 6 shipped, 3 placed) |
| **Total recognised revenue** | **$14,364.45** (sum of successful payments on completed orders) |

The data generator adds 2-4 orders per run but **deliberately skips
`raw_payments`**, so recognised revenue stays at $14,364.45 however many times it
runs. Monthly totals are only a few hundred dollars each and shift with the
generator, so avoid quoting a "last month" figure from a slide.

---

## How this repo stays correct

Competitive content decays. Databricks renamed DLT to Lakeflow pipelines, Asset
Bundles to Declarative Automation Bundles, and Genie spaces to Genie Agents inside
eighteen months. Four mechanisms keep this repo from quietly going stale:

| Mechanism | What it does | When it runs |
|---|---|---|
| **Citations** | Every competitive capability claim carries a `[^claim-id]` footnote resolving to `sources.yml`. The Sources block at the bottom of each doc is **generated** - edit `sources.yml`, not the footnotes | `scripts/build_citations.py` |
| **Naming lint** | Fails the build on retired product names in prose. Prose-only: code, filenames, URLs, `COALESCE()` and "formerly X" clauses are never violations | every PR |
| **Expiry gate** | Every doc carries `expires` front matter (90 days). Past it, CI fails until someone re-verifies and bumps the date | every PR |
| **Source freshness** | HEAD-requests every cited URL and opens a tracking issue when one 404s or redirects to a different path | weekly, Mondays |
| **Fact check** | Recomputes model/metric counts and the revenue figure from the repo and seed data; fails if `facts.yml` drifts or a known-fabricated figure reappears | every PR |

Run them all locally before pushing:

```bash
python3 scripts/naming_lint.py
python3 scripts/build_citations.py --check
python3 scripts/check_expiry.py --strict
python3 scripts/check_facts.py --check
python3 scripts/check_sources.py      # network
```

**The release ritual.** After each Databricks DBR release and each dbt platform
release, one person spends 30 minutes on the diff, updates `sources.yml`, and bumps
`last_verified` / `expires`. Nothing here decays gracefully on its own.

---

## Quickstart (30 min to live demo)

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- SQL Warehouse (serverless recommended)
- dbt platform account (Team or Enterprise plan for Mesh cross-project refs; 14-day trial includes all features)

### Step 1: Load raw data

Import `databricks/notebooks/00_setup_raw_data.py` into your Databricks workspace
and run it. This creates `enablement.ecommerce` with 6 raw Delta tables (dbt uses
5 of them as sources; `raw_reviews` feeds the Lakeflow/Genie portion of the demo).

### Step 2: Run the Lakeflow pipeline

Import `databricks/notebooks/01_lakeflow_pipeline.py` into Databricks,
create a Lakeflow pipeline targeting `enablement.ecommerce_lakeflow`, and run it.
Expected: 13 tables created (5 bronze + 5 silver + 3 gold).

### Step 3: Connect dbt platform and build all 4 projects

In dbt platform:
1. Create a Databricks connection (host, HTTP path, token)
2. Create 4 projects: `platform`, `marketing`, `finance`, `data_science` - each pointing to the corresponding subdirectory (or separate repos)
3. Set project dependencies: `marketing`, `finance`, and `data_science` all depend on `platform`
4. Run the `platform - full build` job first, then consumer jobs

Expected: `dim_customers`, `dim_products`, `fct_orders` in `enablement.ecommerce`;
`mart_customer_segments`, `mart_country_performance` in `enablement.ecommerce_marketing`;
`fct_revenue`, `fct_revenue_by_product` in `enablement.ecommerce_finance`;
`rfm_customer_features`, `customer_churn_features`, `payment_method_affinity_pairs` in `enablement.ecommerce_data_science`.

### Step 4: Create Metric Views

Metric Views are YAML definitions, not SQL DDL. Create them in the Databricks UI:

1. **New → Metric view** (or Catalog → Create → Metric view)
2. Paste `databricks/notebooks/02a_metric_view_orders.yml` → save as `enablement.ecommerce_metric_views.orders_metrics`
3. Paste `databricks/notebooks/02b_metric_view_customers.yml` → save as `enablement.ecommerce_metric_views.customer_metrics`
4. Run `databricks/notebooks/02_metric_views.sql` in the SQL Editor to verify the underlying data.

### Step 5: Create Genie Agents

Follow the instructions in `databricks/genie/`:
- `genie_raw_instructions.md` - Act 1 space
- `genie_lakeflow_instructions.md` - Act 3 space
- `genie_dbt_instructions.md` - Act 4 space

### Step 6: Run the demo

Open `DEMO_SCRIPT.md` and follow the 5-act structure.

---

## Architecture

```
Fivetran ingest + MDLS ─▶ Unity Catalog (open Delta/Iceberg) ─▶ dbt platform (Fusion)
  700+ connectors            Lakeflow (streaming/Spark)          Tested Marts + Mesh
                                                                 Semantic Layer + metric views
                                                                        │
                                                                        ▼
        operational tools ◀── Fivetran Activations ◀── Databricks AI (Genie / agents)
        (Salesforce, HubSpot)     (reverse ETL)         consume the governed layer
```

The complete governed loop - ingest → govern → activate - on the Databricks lakehouse.
See `docs/architecture.md` for the full ASCII + Mermaid diagrams and
`FIVETRAN_DBT_DATABRICKS.md` for the Fivetran + dbt positioning.

---

## Deployment Options

This repo supports two deployment paths:

| Method | Best for | Guide |
|---|---|---|
| **dbt platform** (recommended) | Full governance: Semantic Layer, Catalog, Mesh, Fusion, CI/CD | `SETUP.md` Part D |
| **Declarative Automation Bundles + CI/CD** | Self-managed IaC deployment on Lakeflow Jobs | `docs/dabs_cicd_guide.md` |

The Declarative Automation Bundle path deploys dbt Core on Databricks compute via `databricks.yml`
and a GitHub Actions pipeline. It handles execution but does **not** include
the Semantic Layer, Catalog, or Mesh -- those require dbt platform.

For the 5-act demo, use dbt platform. For customers who want IaC-managed
deployment alongside dbt platform, use both (see the hybrid pattern in
`docs/dabs_cicd_guide.md` Part 8).

```bash
# Quick start with Declarative Automation Bundles (after configuring databricks.yml)
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev platform_dbt_job
```

---

## The Core Message

**dbt and Databricks are AND, not OR.**

- Databricks: compute, storage, orchestration, and AI (Genie, agents) on the lakehouse
- Fivetran + dbt (one company since 2026-06-01): the governed data layer - ingestion +
  Managed Data Lake Service, then tested, documented, version-controlled business logic,
  then activation (reverse ETL) back to operational tools
- Together: Genie answers that are accurate, consistent, and auditable - and governed
  data that reaches the tools the business works in

For competitive SA enablement - where Fivetran + dbt win the data layer on faster
time-to-value and a better-governed layer for Databricks AI - see
`FIVETRAN_DBT_DATABRICKS.md`.

The demo proves this by showing Genie quality improving at each stage:
1. Raw tables → ambiguous, unauditable answers
2. Lakeflow gold → better, but manual metadata
3. dbt marts + semantic layer → accurate, consistent, PR-reviewed definitions

---

## Repo Structure (Full)

```
dbt-dbx-field-enablement/
├── README.md
├── SETUP.md
├── DEMO_SCRIPT.md
├── BATTLE_CARD.md
├── METRIC_VIEWS_COMPARISON.md
├── FAQ.md
├── databricks.yml               # Declarative Automation Bundle config
├── resources/
│   └── dbt_job.yml              # dbt job definition (IaC)
├── dbt_profiles/
│   └── profiles.yml             # Profiles for bundle deployment (OAuth)
├── .github/
│   └── workflows/
│       └── deploy-dbt.yml       # CI/CD pipeline (GitHub Actions)
├── platform/                    # Producer dbt project
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/             # 9 staging models (5 e-commerce + 4 Salesforce)
│   │   ├── intermediate/        # 2 intermediate models
│   │   ├── marts/               # 3 contracted public models + crm/ (3 more)
│   │   ├── metrics/             # orders_metric_view.sql (materialized='metric_view')
│   │   ├── semantic/            # cross-model ratio + derived metrics
│   │   └── groups.yml
│   └── tests/
│       └── assert_positive_revenue.sql
├── marketing/                   # Consumer dbt project (Mesh)
│   ├── dbt_project.yml
│   ├── dependencies.yml
│   ├── profiles.yml
│   └── models/
│       ├── mart_customer_segments.sql
│       └── mart_country_performance.sql
├── finance/                     # Consumer dbt project (Mesh)
│   ├── dbt_project.yml
│   ├── dependencies.yml
│   ├── profiles.yml
│   └── models/
│       ├── fct_revenue.sql
│       └── fct_revenue_by_product.sql
├── data_science/                # Consumer dbt project (Mesh + Python models)
│   ├── dbt_project.yml
│   ├── dependencies.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       │   └── stg_customer_order_history.sql
│       ├── features/
│       │   ├── rfm_customer_features.py      (PySpark RFM scoring)
│       │   └── customer_churn_features.py    (PySpark churn features)
│       └── marts/
│           └── payment_method_affinity_pairs.py  (PySpark affinity analysis)
├── databricks/
│   ├── notebooks/
│   │   ├── 00_setup_raw_data.py
│   │   ├── 01_lakeflow_pipeline.sql        (platform pipeline - SQL)
│   │   ├── 02_metric_views.sql
│   │   ├── 03_data_generator.py
│   │   ├── 04_lakeflow_mesh_equivalent.py  (reference - combined Python view)
│   │   ├── 04a_lakeflow_marketing.sql      (marketing team pipeline - SQL)
│   │   ├── 04b_lakeflow_finance.sql        (finance team pipeline - SQL)
│   │   └── 05a_lakeflow_data_science.py   (DS team pipeline - duplication contrast)
│   ├── genie/
│   │   ├── genie_raw_instructions.md
│   │   ├── genie_lakeflow_instructions.md
│   │   ├── genie_dbt_instructions.md
│   │   └── genie_demo_queries.md
│   └── app/
│       ├── app.py
│       ├── app.yml
│       └── requirements.txt
├── docs/
│   ├── architecture.md
│   ├── mesh_explainer.md
│   ├── fusion_cheat_sheet.md
│   └── dabs_cicd_guide.md          # DABs + CI/CD guide with Declarative comparison
└── .gitignore
```

---

## Verification Checklist

- [ ] dbt platform: `platform - full build` job → green, 10 models, all tests pass
- [ ] dbt platform: `marketing - full build` job → green, 2 models in `enablement.ecommerce_marketing`
- [ ] dbt platform: `finance - full build` job → green, 2 models in `enablement.ecommerce_finance`
- [ ] dbt platform: `data_science - full build` job → green, 4 models in `enablement.ecommerce_data_science`
- [ ] Lakeflow pipeline → 13 tables in `enablement.ecommerce_lakeflow`
- [ ] Lakeflow marketing + finance pipelines → 4 tables across 2 schemas (contrast demo)
- [ ] Lakeflow data science pipeline → 2 tables in `enablement.ecommerce_lakeflow_ds` (Act 4f contrast)
- [ ] `02_metric_views.sql` → views created in `enablement.ecommerce_metric_views`
- [ ] All 3 Genie Agents created and returning answers to demo queries
- [ ] Databricks App deployed, all 4 tabs rendering

---

## Related Repos

- `dbt-databricks-enablement/` - original single-project enablement demo
- `dbt-mesh-fusion/` - original Mesh + Fusion demo

This repo consolidates both with a focus on the Genie / Semantic Layer story
and a structured 5-act demo format.
# dbt-dbx-field-enablement
