# Classroom Setup Guide

This guide is for instructors and participants running this demo in a **multi-user classroom** where everyone shares the same Databricks workspace.

---

## How isolation works

Every participant gets their own namespace automatically. No two people will write to the same tables.

| Resource | Isolation mechanism | Example for user `alice.martin@company.com` |
|---|---|---|
| Raw data schema | `ecommerce_<username>` derived from `current_user()` | `enablement.ecommerce_alice_martin` |
| dbt output schema | Same -- set via `DBT_SCHEMA` env var | `enablement.ecommerce_alice_martin` |
| DLT pipeline output | Each user creates their own pipeline with their own schema | `enablement.ecommerce_alice_martin_lakeflow` |
| DLT consumer pipelines | Per-user pipeline + schema | `enablement.ecommerce_alice_martin_lakeflow_marketing` |
| DABs bundle (dev) | Auto-appends username via `${workspace.current_user.short_name}` | `ecommerce_dev_alice_martin` |
| dbt Databricks Job | Dev mode auto-prefixes job name with `[dev alice_martin]` | `[dev alice_martin] dbt platform build - dev` |
| Metric views | Each user saves to their own schema | `enablement.ecommerce_alice_martin_metric_views` |

The **catalog** (`enablement`) is shared. Only **schemas** are per-user.

---

## Can multiple developers work simultaneously on Databricks?

**Yes.** Here's how each layer handles concurrency:

### SQL Warehouses (shared, auto-scaling)
- **Serverless warehouses** scale automatically -- 30 participants can query simultaneously
- Each query runs in isolation; there's no cross-query interference
- Recommendation: use a single **Serverless SQL Warehouse** for the entire class

### Compute clusters
- Each user can use **Serverless compute** (auto-provisions per-user)
- Or share a **multi-user cluster** (Unity Catalog enforces data isolation)
- DLT pipelines provision their own compute -- no cluster sharing concerns

### Unity Catalog (namespace isolation)
- Per-user schemas prevent write collisions -- two users will never write to the same table
- The shared catalog (`enablement`) is safe because `CREATE SCHEMA IF NOT EXISTS` is idempotent
- Unity Catalog permissions can restrict who creates schemas if needed

### dbt (schema-level isolation)
- Each user targets their own schema via `DBT_SCHEMA` env var
- `dbt build` writes only to that user's schema
- Source freshness, tests, and docs all work independently per-schema

### DLT pipelines (pipeline-level isolation)
- Each user creates their own named pipeline (e.g., `ecommerce-lakeflow-alice`)
- Pipeline output goes to the user's own schema
- Pipelines have their own compute -- no resource sharing

### Git / dbt Cloud (project-level isolation)
- Each user can have their own branch or dbt Cloud dev environment
- dbt Cloud dev credentials target per-user schemas

### What can still collide?
- **Catalog creation**: `CREATE CATALOG IF NOT EXISTS enablement` is safe -- idempotent
- **Cluster startup**: Many users starting clusters at once may hit cloud provider limits. Use serverless to avoid this.
- **Warehouse queue**: A single small warehouse serving 30 users will queue. Size it at Medium+ or use serverless.

---

## Participant quickstart (5 minutes)

### Step 1: Run the setup notebook

Open `databricks/notebooks/00_setup_raw_data` and click **Run All**.

It auto-detects your username and prints:
```
=== Your namespace: enablement.ecommerce_alice_martin ===
=== User: alice.martin@company.com ===

For dbt, set in your .env:
  DBT_CATALOG=enablement
  DBT_SCHEMA=ecommerce_alice_martin

For DLT pipelines, add to pipeline configuration:
  source_catalog = enablement
  source_schema  = ecommerce_alice_martin
```

**Write down your schema name** -- you'll use it in every subsequent step.

### Step 2: Configure dbt

```bash
cp .env.example .env
```

Edit `.env` and set:
```
DBT_CATALOG=enablement
DBT_SCHEMA=ecommerce_alice_martin   # <-- your schema from Step 1
```

Then:
```bash
source .env
cd platform && dbt deps && dbt build
```

### Step 3: Create your DLT pipeline

1. **Jobs & Pipelines** > **Create** > **ETL pipeline**
2. Name: `ecommerce-lakeflow-<yourname>` (e.g., `ecommerce-lakeflow-alice`)
3. Catalog: `enablement`
4. Schema: `ecommerce_<yourname>_lakeflow` (e.g., `ecommerce_alice_martin_lakeflow`)
5. **Configuration** > Add:
   - `source_catalog` = `enablement`
   - `source_schema` = `ecommerce_<yourname>` (your schema from Step 1)
6. Add notebook `01_lakeflow_pipeline.py` > **Start**

### Step 4: Schedule the data generator (optional)

1. **Jobs & Pipelines** > **Create** > **Job**
2. Task type: Notebook
3. Notebook: `databricks/notebooks/03_data_generator`
4. The schema auto-derives from your username -- no extra config needed
5. Schedule: Every 30 minutes

### Step 5: Run dbt source freshness (after 2+ days)

```bash
cd platform && dbt source freshness
```

`raw_payments` will show as stale (the data generator deliberately skips it).

---

## Instructor pre-flight checklist

Before the class:

- [ ] **Catalog exists**: `CREATE CATALOG IF NOT EXISTS enablement` (needs metastore admin)
- [ ] **Participants have**: `USE CATALOG`, `CREATE SCHEMA`, `USE SCHEMA` grants on `enablement`
- [ ] **SQL Warehouse**: Serverless warehouse available (or Medium+ classic warehouse)
- [ ] **Unity Catalog enabled**: Required for catalog/schema isolation
- [ ] **DLT enabled**: Participants need permission to create DLT pipelines
- [ ] **Test with 2 accounts**: Run the full setup with two different users to verify isolation

Grant template:
```sql
-- Run as metastore admin or catalog owner
CREATE CATALOG IF NOT EXISTS enablement;
GRANT USE CATALOG ON CATALOG enablement TO `classroom-participants`;
GRANT CREATE SCHEMA ON CATALOG enablement TO `classroom-participants`;
```

---

## Cleanup after class

Run as catalog admin to remove all participant schemas:

```sql
-- List all participant schemas
SHOW SCHEMAS IN enablement LIKE 'ecommerce_%';

-- Drop a specific participant's schemas
DROP SCHEMA IF EXISTS enablement.ecommerce_alice_martin CASCADE;
DROP SCHEMA IF EXISTS enablement.ecommerce_alice_martin_lakeflow CASCADE;
DROP SCHEMA IF EXISTS enablement.ecommerce_alice_martin_lakeflow_marketing CASCADE;
DROP SCHEMA IF EXISTS enablement.ecommerce_alice_martin_lakeflow_finance CASCADE;

-- Or drop everything at once (careful!)
-- DROP CATALOG enablement CASCADE;
```

Delete participant DLT pipelines and jobs manually from the Workflows UI.
