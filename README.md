# dbt + Databricks Field Enablement

A consolidated, demo-ready repo for dbt SAs and AEs enabling colleagues on
the dbt + Databricks joint story. Covers dbt Fusion, Genie + Semantic Layer,
dbt Mesh governance, and an honest Databricks Metric Views comparison.

---

## What's in This Repo

| File / Directory | Purpose |
|---|---|
| `DEMO_SCRIPT.md` | 5-act, 20–25 min demo script with timing, talking points, Q&A anchors |
| `BATTLE_CARD.md` | 12 competitive concerns with factual responses and demo proof points |
| `METRIC_VIEWS_COMPARISON.md` | Honest dbt Semantic Layer vs Databricks Metric Views comparison |
| `FAQ.md` | Objection handling for customers, champions, and Databricks SAs |
| `SETUP.md` | Full environment setup — DBX workspace + dbt Cloud + Mesh |
| `platform/` | Producer dbt project (Fusion-conformant, contracts, semantic layer) |
| `marketing/` | Consumer dbt project — cross-project refs from platform |
| `finance/` | Consumer dbt project — cross-project refs from platform |
| `databricks/notebooks/` | Setup + Lakeflow pipeline + Metric Views SQL + data generator + Mesh equivalent demo |
| `databricks/genie/` | Genie Space configs + demo queries for all 3 acts |
| `databricks/app/` | Streamlit app (4 tabs) for the Databricks App deployment |
| `docs/` | Architecture diagrams, Mesh explainer, Fusion cheat sheet |

---

## Quickstart (30 min to live demo)

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- SQL Warehouse (serverless recommended)
- dbt Cloud account (Team or Enterprise plan for Mesh cross-project refs; 14-day trial includes all features)

### Step 1: Load raw data

Import `databricks/notebooks/00_setup_raw_data.py` into your Databricks workspace
and run it. This creates `enablement.ecommerce` with 5 raw Delta tables.

### Step 2: Run the Lakeflow pipeline

Import `databricks/notebooks/01_lakeflow_pipeline.py` into Databricks,
create a DLT pipeline targeting `enablement.ecommerce_lakeflow`, and run it.
Expected: 13 tables created (5 bronze + 5 silver + 3 gold).

### Step 3: Connect dbt Cloud and build all 3 projects

In dbt Cloud:
1. Create a Databricks connection (host, HTTP path, token)
2. Create 3 projects: `platform`, `marketing`, `finance` — each pointing to the corresponding subdirectory (or separate repos)
3. Set project dependencies: `marketing` and `finance` both depend on `platform`
4. Run the `platform - full build` job first, then consumer jobs

Expected: `dim_customers`, `dim_products`, `fct_orders` in `enablement.ecommerce`;
`mart_customer_segments`, `mart_country_performance` in `enablement.ecommerce_marketing`;
`fct_revenue`, `fct_revenue_by_product` in `enablement.ecommerce_finance`.

### Step 4: Create Metric Views

Metric Views are YAML definitions, not SQL DDL. Create them in the Databricks UI:

1. **New → Metric view** (or Catalog → Create → Metric view)
2. Paste `databricks/notebooks/02a_metric_view_orders.yml` → save as `enablement.ecommerce_metric_views.orders_metrics`
3. Paste `databricks/notebooks/02b_metric_view_customers.yml` → save as `enablement.ecommerce_metric_views.customer_metrics`
4. Run `databricks/notebooks/02_metric_views.sql` in the SQL Editor to verify the underlying data.

### Step 5: Create Genie Spaces

Follow the instructions in `databricks/genie/`:
- `genie_raw_instructions.md` — Act 1 space
- `genie_lakeflow_instructions.md` — Act 3 space
- `genie_dbt_instructions.md` — Act 4 space

### Step 6: Run the demo

Open `DEMO_SCRIPT.md` and follow the 5-act structure.

---

## Architecture

```
Raw Delta Tables → dbt Cloud (Fusion compiler) → Tested Marts → Semantic Layer → Genie
                      ↓               ↓
               Lakeflow DLT    dbt Mesh Consumers
               (Bronze/Silver)  (marketing, finance)
```

See `docs/architecture.md` for the full ASCII + Mermaid diagrams.

---

## The Core Message

**dbt and Databricks are AND, not OR.**

- Databricks: compute, storage, orchestration, Lakeflow for ingestion
- dbt: governance layer — tested, documented, version-controlled business logic
- Together: Genie answers that are accurate, consistent, and auditable

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
├── platform/                    # Producer dbt project
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/             # 5 staging models + sources + schema
│   │   ├── intermediate/        # 2 intermediate models
│   │   ├── marts/               # 3 public models with contracts
│   │   ├── semantic/            # MetricFlow semantic models + 12 metrics
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
├── databricks/
│   ├── notebooks/
│   │   ├── 00_setup_raw_data.py
│   │   ├── 01_lakeflow_pipeline.sql        (platform pipeline — SQL)
│   │   ├── 02_metric_views.sql
│   │   ├── 03_data_generator.py
│   │   ├── 04_lakeflow_mesh_equivalent.py  (reference — combined Python view)
│   │   ├── 04a_lakeflow_marketing.sql      (marketing team pipeline — SQL)
│   │   └── 04b_lakeflow_finance.sql        (finance team pipeline — SQL)
│   ├── genie/
│   │   ├── genie_raw_instructions.md
│   │   ├── genie_lakeflow_instructions.md
│   │   ├── genie_dbt_instructions.md
│   │   └── genie_demo_queries.md
│   └── app/
│       ├── app.py
│       ├── app.yml
│       └── requirements.txt
└── docs/
    ├── architecture.md
    ├── mesh_explainer.md
    └── fusion_cheat_sheet.md
```

---

## Verification Checklist

- [ ] dbt Cloud: `platform - full build` job → green, 10 models, all tests pass
- [ ] dbt Cloud: `marketing - full build` job → green, 2 models in `enablement.ecommerce_marketing`
- [ ] dbt Cloud: `finance - full build` job → green, 2 models in `enablement.ecommerce_finance`
- [ ] Lakeflow pipeline → 13 tables in `enablement.ecommerce_lakeflow`
- [ ] Lakeflow marketing + finance pipelines → 4 tables across 2 schemas (contrast demo)
- [ ] `02_metric_views.sql` → views created in `enablement.ecommerce_metric_views`
- [ ] All 3 Genie Spaces created and returning answers to demo queries
- [ ] Databricks App deployed, all 4 tabs rendering

---

## Related Repos

- `dbt-databricks-enablement/` — original single-project enablement demo
- `dbt-mesh-fusion/` — original Mesh + Fusion demo

This repo consolidates both with a focus on the Genie / Semantic Layer story
and a structured 5-act demo format.
# dbt-dbx-field-enablement
