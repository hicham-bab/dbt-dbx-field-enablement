# dbt + Databricks Field Enablement

A consolidated, demo-ready repo for dbt SAs and AEs enabling colleagues on
the dbt + Databricks joint story. Covers dbt Fusion, Genie + Semantic Layer,
dbt Mesh governance, and an honest Databricks metric views comparison.

> **Naming note (2026):** This repo uses **dbt platform** (the managed product,
> formerly dbt Cloud) and the current **Lakeflow** names (Lakeflow Jobs, Lakeflow
> Declarative Pipelines). The AI assistant is **dbt Wizard**. Product naming is
> still in transition — confirm the latest terms with PMM before external use.

---

## What's in This Repo

| File / Directory | Purpose |
|---|---|
| `DEMO_SCRIPT.md` | 5-act, 20–25 min demo script with timing, talking points, Q&A anchors |
| `BATTLE_CARD.md` | 12 competitive concerns with factual responses and demo proof points |
| `METRIC_VIEWS_COMPARISON.md` | Honest dbt Semantic Layer vs Databricks Metric Views comparison |
| `FAQ.md` | Objection handling for customers, champions, and Databricks SAs |
| `SETUP.md` | Full environment setup — DBX workspace + dbt platform + Mesh |
| `platform/` | Producer dbt project (Fusion-conformant, contracts, semantic layer) |
| `marketing/` | Consumer dbt project — cross-project refs from platform |
| `finance/` | Consumer dbt project — cross-project refs from platform |
| `data_science/` | Consumer dbt project — Python models, DS features via Mesh |
| `databricks/notebooks/` | Setup + Lakeflow pipeline + Metric Views SQL + data generator + Mesh equivalent demo |
| `databricks/genie/` | Genie Space configs + demo queries for all 3 acts |
| `databricks/app/` | Streamlit app (4 tabs) for the Databricks App deployment |
| `docs/` | Architecture diagrams, Mesh explainer, Fusion cheat sheet, DABs CI/CD guide |
| `databricks.yml` | Declarative Asset Bundle configuration (IaC for Databricks Jobs) |
| `resources/` | Bundle resource definitions (dbt job YAML) |
| `dbt_profiles/` | dbt profiles for Asset Bundle deployments (OAuth M2M) |
| `.github/workflows/` | CI/CD pipeline (GitHub Actions: validate -> deploy -> run) |

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
2. Create 4 projects: `platform`, `marketing`, `finance`, `data_science` — each pointing to the corresponding subdirectory (or separate repos)
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
Raw Delta Tables → dbt platform (Fusion engine) → Tested Marts → Semantic Layer → Genie
                      ↓               ↓
               Lakeflow Declarative Pipelines    dbt Mesh Consumers
               (Bronze/Silver)  (marketing, finance, data_science)
                                        ↑
                                  Python models (PySpark)
                                  on Databricks compute
```

See `docs/architecture.md` for the full ASCII + Mermaid diagrams.

---

## Deployment Options

This repo supports two deployment paths:

| Method | Best for | Guide |
|---|---|---|
| **dbt platform** (recommended) | Full governance: Semantic Layer, Explorer, Mesh, Fusion, CI/CD | `SETUP.md` Part D |
| **Declarative Asset Bundles + CI/CD** | Self-managed IaC deployment on Lakeflow Jobs | `docs/dabs_cicd_guide.md` |

The Asset Bundle path deploys dbt Core on Databricks compute via `databricks.yml`
and a GitHub Actions pipeline. It handles execution but does **not** include
the Semantic Layer, Explorer, or Mesh -- those require dbt platform.

For the 5-act demo, use dbt platform. For customers who want IaC-managed
deployment alongside dbt platform, use both (see the hybrid pattern in
`docs/dabs_cicd_guide.md` Part 8).

```bash
# Quick start with Asset Bundles (after configuring databricks.yml)
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev platform_dbt_job
```

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
├── databricks.yml               # Declarative Asset Bundle config
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
│   │   ├── 01_lakeflow_pipeline.sql        (platform pipeline — SQL)
│   │   ├── 02_metric_views.sql
│   │   ├── 03_data_generator.py
│   │   ├── 04_lakeflow_mesh_equivalent.py  (reference — combined Python view)
│   │   ├── 04a_lakeflow_marketing.sql      (marketing team pipeline — SQL)
│   │   ├── 04b_lakeflow_finance.sql        (finance team pipeline — SQL)
│   │   └── 05a_lakeflow_data_science.py   (DS team pipeline — duplication contrast)
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
- [ ] All 3 Genie Spaces created and returning answers to demo queries
- [ ] Databricks App deployed, all 4 tabs rendering

---

## Related Repos

- `dbt-databricks-enablement/` — original single-project enablement demo
- `dbt-mesh-fusion/` — original Mesh + Fusion demo

This repo consolidates both with a focus on the Genie / Semantic Layer story
and a structured 5-act demo format.
# dbt-dbx-field-enablement
