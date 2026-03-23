# Quickstart — dbt + Databricks Field Enablement

**Goal:** Go from zero to a live 5-act demo in ~55 minutes.
**Prerequisites:** A Databricks workspace with Unity Catalog enabled. That's it.

---

## Overview

| Part | What you do | Time |
|------|-------------|------|
| A | Gather Databricks credentials (host, warehouse, token) | 10 min |
| B | Load raw Delta tables via notebook | 5 min |
| C | Run the Lakeflow DLT pipeline (13 tables) | 10 min |
| D | Connect dbt Cloud and build all 3 dbt projects (platform + Mesh consumers) | 20 min |
| E | Schedule the data generator (source freshness demo) | 5 min |
| F | Create Databricks Metric Views | 3 min |
| G | Create 3 Genie Spaces and test them | 10 min |
| H | Deploy the Streamlit app (optional) | 5 min |

---

## Part A: Gather Databricks Credentials

You need three values before touching any code. Collect them first.

---

### A1. Verify Unity Catalog is enabled

Unity Catalog must be enabled on your workspace. To check:

1. Go to your workspace home page
2. Top-right avatar → **Settings**
3. Left sidebar → **Admin Console** (requires admin role, or ask your workspace admin)
4. **Unity Catalog** tab → Status should show **Enabled** (green)

If UC is not enabled, request a demo workspace from your Databricks SE — do not try
to enable it yourself on a shared workspace without checking with the workspace admin.

**Minimum permissions you need:**
- `CREATE CATALOG` — to create the `enablement` catalog
- `USE CATALOG` and `CREATE SCHEMA` — to create schemas inside it
- Access to a SQL Warehouse

If you are unsure about permissions, run this in the SQL Editor:
```sql
SHOW GRANTS ON CATALOG enablement;
-- If this errors with "catalog not found", you need CREATE CATALOG to proceed
```

---

### A2. Create a SQL Warehouse

dbt Cloud connects to a Databricks SQL Warehouse to execute models. You need its HTTP path.

1. Left sidebar → **SQL Warehouses**
2. Click **Create SQL Warehouse** (top right)
3. Fill in:
   - **Name:** `enablement-demo` (or any name you'll recognize)
   - **Cluster size:** 2X-Small is sufficient for this demo dataset (10 customers, 15 orders)
   - **Type:** Select **Serverless** — this avoids cluster startup time during the demo
     - If Serverless is not available in your workspace, choose **Pro**
4. Click **Create** and wait for it to start (green dot = running)
5. Once running, click into the warehouse → **Connection details** tab

You will see:
```
Server hostname:   adb-1234567890123456.1.azuredatabricks.net
HTTP path:         /sql/1.0/warehouses/abc1234567890def
```

**Copy both values** — you will need them when creating the dbt Cloud connection in Part D.

> Tip: If a warehouse already exists and is running, you can reuse it. Just grab
> the HTTP path from Connection details.

---

### A3. Generate a Personal Access Token

dbt Cloud authenticates with Databricks using a PAT. OAuth is also supported but
PAT is simpler to configure.

1. Top-right avatar → **Settings**
2. Left sidebar → **Developer**
3. Click **Manage** next to "Access tokens"
4. Click **Generate new token**
5. Fill in:
   - **Comment:** `dbt-demo`
   - **Lifetime (days):** 90 (or longer for repeated use)
6. Click **Generate**
7. **Copy the token immediately** — it starts with `dapi` and is shown only once

If you close the dialog without copying it, you must generate a new one.

---

### A4. Record your workspace hostname

Your workspace hostname is the domain portion of your workspace URL.

Examples:
- `https://adb-1234567890123456.1.azuredatabricks.net` → hostname is `adb-1234567890123456.1.azuredatabricks.net`
- `https://mycompany.azuredatabricks.net` → hostname is `mycompany.azuredatabricks.net`

Do **not** include `https://`. dbt and the Databricks CLI use the bare hostname.

---

### A5. Credentials summary

Before moving on, you should have all three:

```
DBX_HOST      = adb-xxxxxxxxxxxxxxxx.x.azuredatabricks.net   (no https://)
DBX_HTTP_PATH = /sql/1.0/warehouses/xxxxxxxxxxxxxxxx
DBX_TOKEN     = dapixxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Part B: Load Raw Data

This step creates the `enablement.ecommerce` catalog/schema and seeds it with
5 raw Delta tables (10 customers, 15 orders, 20 order items, 10 products, 15 payments).

---

### B1. Upload the setup notebook to Databricks

1. In Databricks, click **Workspace** in the left sidebar
2. Navigate to a folder where you want to store demo notebooks
   (e.g., your personal folder: `Users/your.email@company.com/`)
3. Click the **⋮** (three dots) next to the folder → **Import**
4. Select **File**
5. Upload `databricks/notebooks/00_setup_raw_data.py` from this repo
6. Click **Import**

The notebook will open automatically.

---

### B2. Attach a cluster and run

The setup notebook uses `%sql` magic and does not require a DLT pipeline —
you can run it on any cluster or a SQL Warehouse.

1. At the top of the notebook, click **Connect** (or the cluster dropdown)
2. Select your SQL Warehouse or any running cluster
   - If nothing is running, start any available cluster (Runtime 13.3 LTS or later)
3. Click **Run all** (top toolbar, play button → "Run all")

Watch the cells execute. Each cell creates one table and inserts rows.

---

### B3. Verify the raw tables exist

After the notebook finishes (< 1 minute), the last cell runs a verification query.

**Expected output:**

| tbl | rows |
|---|---|
| raw_customers | 10 |
| raw_orders | 15 |
| raw_order_items | 20 |
| raw_products | 10 |
| raw_payments | 15 |

You can also verify in the SQL Editor:
```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_catalog = 'enablement'
  AND table_schema = 'ecommerce'
ORDER BY table_name;
```

Expected: 5 rows — `raw_customers`, `raw_order_items`, `raw_orders`, `raw_payments`, `raw_products`.

If you see an error like `PERMISSION_DENIED: User does not have CREATE SCHEMA privilege`,
ask your workspace admin to grant you `CREATE SCHEMA ON CATALOG enablement` — or
ask them to create the `enablement.ecommerce` schema and grant you `CREATE TABLE` on it.

---

## Part C: Run the Lakeflow Pipeline

This step creates the DLT medallion pipeline: 5 bronze + 5 silver + 3 gold tables
in `enablement.ecommerce_lakeflow`. This is the "Act 3" dataset for the demo.

---

### C1. Upload the pipeline file

1. **Workspace** → navigate to same folder as before
2. **Import** → **File** → upload `databricks/notebooks/01_lakeflow_pipeline.sql`
3. Note the full path after importing (e.g., `/Users/you/01_lakeflow_pipeline`)

---

### C2. Create the pipeline

The new Databricks UI creates the pipeline shell first, then asks you to add code.

**Step 1 — Create the pipeline shell:**

1. Left sidebar → **Jobs & Pipelines**
2. Click **Create** (top right) → **ETL pipeline**
3. A dialog opens — fill in:

| Field | Value |
|---|---|
| Pipeline name | `ecommerce-lakeflow-demo` |
| Catalog | `enablement` |
| Target schema | `ecommerce_lakeflow` |

4. Click **Create**

**Step 2 — Add the notebook as the source code:**

You land on the "Next step for your pipeline" screen. Click **Add existing assets**.

1. Click **Add existing assets**
   *(opens "Add existing source code" dialog)*
2. In the file browser, navigate to the notebook you uploaded in C1
   (e.g., `Users/your.email/01_lakeflow_pipeline`)
3. Select it and confirm

The notebook now appears in the pipeline editor. You should see the Python file
listed in the left panel.

---

### C3. Start the pipeline and monitor

1. Click **Start** (top right of the pipeline editor)
2. The pipeline will:
   - Allocate a cluster (~2–3 min if not serverless)
   - Execute all table functions in dependency order
   - Show a DAG visualization as tables complete (bronze → silver → gold)

Watch for the green checkmarks. Each table node in the DAG turns green when complete.

**Expected total runtime:** 3–6 minutes (faster with serverless)

---

### C4. Verify the 13 tables

Once the pipeline status shows **Completed** (green banner at top):

```sql
-- In SQL Editor
SHOW TABLES IN enablement.ecommerce_lakeflow;
```

Expected 13 tables:

| Layer | Tables |
|---|---|
| Bronze | `bronze_customers`, `bronze_orders`, `bronze_order_items`, `bronze_products`, `bronze_payments` |
| Silver | `silver_customers`, `silver_orders`, `silver_order_items`, `silver_products`, `silver_payments` |
| Gold | `gold_dim_customers`, `gold_fct_orders`, `gold_fct_revenue` |

Spot-check the gold layer:
```sql
SELECT customer_segment, COUNT(*) AS n
FROM enablement.ecommerce_lakeflow.gold_dim_customers
GROUP BY customer_segment;
-- Expected: 3 rows — high_value, mid_value, low_value
```

---

### C5. Run the Mesh equivalent pipelines (demo contrast)

This step is optional but highly recommended — it makes the dbt Mesh vs Lakeflow
comparison concrete and visible, not just theoretical.

Two separate notebooks, one per team. Each gets its own pipeline and its own schema —
mirroring the fact that in Lakeflow, each team would own and maintain their own pipeline.

**Upload both notebooks:**

1. **Workspace** → **Import** → **File** → upload `databricks/notebooks/04a_lakeflow_marketing.sql`
2. Repeat for `databricks/notebooks/04b_lakeflow_finance.sql`

**Create the marketing pipeline:**

1. **Jobs & Pipelines** → **Create** → **ETL pipeline**
2. Dialog: name = `ecommerce-lakeflow-marketing`, catalog = `enablement`, schema = `ecommerce_lakeflow_marketing` → **Create**
3. "Next step" screen → **Add existing assets** → select `04a_lakeflow_marketing.sql` → **Add**
4. Click **Start** — creates 2 tables in `enablement.ecommerce_lakeflow_marketing`

**Create the finance pipeline:**

1. **Jobs & Pipelines** → **Create** → **ETL pipeline**
2. Dialog: name = `ecommerce-lakeflow-finance`, catalog = `enablement`, schema = `ecommerce_lakeflow_finance` → **Create**
3. "Next step" screen → **Add existing assets** → select `04b_lakeflow_finance.sql` → **Add**
4. Click **Start** — creates 2 tables in `enablement.ecommerce_lakeflow_finance`

**Expected result — 2 separate schemas, 2 tables each:**

| Schema | Table |
|---|---|
| `ecommerce_lakeflow_marketing` | `marketing_customer_segments` |
| `ecommerce_lakeflow_marketing` | `marketing_country_performance` |
| `ecommerce_lakeflow_finance` | `finance_fct_revenue` |
| `ecommerce_lakeflow_finance` | `finance_fct_revenue_by_product` |

```sql
SHOW TABLES IN enablement.ecommerce_lakeflow_marketing;
SHOW TABLES IN enablement.ecommerce_lakeflow_finance;
```

**What to show in the demo:**

Open `04_lakeflow_mesh_equivalent.py` in the Databricks editor and scroll through it.
Five deliberate problems are embedded with `# DUPLICATION` and `# NOTE:` comments:
1. Customer segmentation thresholds copy-pasted from the platform pipeline
2. Revenue recognition rule duplicated across two tables
3. Finance team bypassing the protected silver layer (no access enforcement)
4. Column metadata manually re-written instead of inherited
5. No formal dependency declaration between pipelines

Then open `finance/models/fct_revenue.sql` in dbt Cloud — it's 8 lines.
The question: "Which would you rather maintain?"

---

## Part D: dbt Cloud Setup (Platform + Mesh Consumers)

This step connects dbt Cloud to your Databricks workspace and builds all three
dbt projects: `platform` (the data producer), and `marketing` + `finance`
(the Mesh consumers). All three run in dbt Cloud — no local CLI required.

> **Plan note:** Cross-project Mesh refs require the **Team** or **Enterprise** plan
> in dbt Cloud. If you are on a trial, all features are available for 14 days.

---

### D1. Access your dbt Cloud account

1. Go to **cloud.getdbt.com**
2. Log in with your dbt Labs SSO (or your customer's dbt Cloud account)
3. If you need a new account: click **Start for free** → complete signup → the trial
   activates all Team/Enterprise features for 14 days

---

### D2. Create the Databricks connection

You create one shared connection that all three projects will use.

1. In dbt Cloud, top-left account menu → **Account settings**
2. Left sidebar → **Connections**
3. Click **New connection**
4. Select **Databricks**
5. Fill in:

| Field | Value |
|---|---|
| Connection name | `enablement-databricks` |
| Server hostname | Your `DBX_HOST` from Part A4 (no `https://`) |
| HTTP path | Your HTTP path from Part A2 |
| OAuth or PAT | Select **Personal Access Token**, paste your token from Part A3 |
| Default catalog | `enablement` |

6. Click **Save** — dbt Cloud will test the connection. You should see a green checkmark.

If the test fails: verify the warehouse is running (not stopped) in Databricks,
and that the hostname does not include `https://`.

---

### D3. Push this repo to a git provider

dbt Cloud reads your project code from a git repository.

**Option A — GitHub (recommended):**
1. Fork or push `dbt-dbx-field-enablement/` to your GitHub account
2. In dbt Cloud → Account settings → **Integrations** → connect to GitHub
3. Authorize dbt Cloud to access your repositories

**Option B — GitLab / Azure DevOps:**
Same flow — dbt Cloud supports all major providers under Account settings → Integrations.

**Option C — dbt Cloud managed git (quickest for demos):**
If you don't want to push to GitHub, dbt Cloud offers a built-in managed git
repository. You can upload files directly via the dbt Cloud IDE.

---

### D4. Create the platform project

1. In dbt Cloud, top-left → **Account settings** → **Projects**
2. Click **New project**
3. Fill in:

| Field | Value |
|---|---|
| Project name | `platform` |
| dbt version | `1.9` (or latest — must be ≥ 1.9 for Fusion compiler) |
| Connection | `enablement-databricks` (created in D2) |
| Repository | Select your repo from D3 |
| Project subdirectory | `platform` |

4. Click **Save**

5. Next: set up an **Environment** for this project:
   - In the project, go to **Deploy** → **Environments** → **New environment**
   - Name: `Production`
   - dbt version: `1.9` (inherit from project)
   - Under **Deployment credentials**: set **Schema** to `ecommerce`
     (the catalog `enablement` is already set by the connection)
   - Click **Save**

---

### D5. Create and run the platform job

1. In the `platform` project → **Deploy** → **Jobs** → **New job** → **Deploy job**
2. Fill in:

| Field | Value |
|---|---|
| Job name | `platform - full build` |
| Environment | `Production` |
| Commands | `dbt deps` then `dbt build` (add both as separate commands) |

3. Click **Save**
4. Click **Run now** (top right of the job page)

Watch the run log. You should see:
1. `dbt deps` — installs `dbt_utils` and `dbt_expectations`
2. Staging views created: `stg_customers`, `stg_orders`, `stg_order_items`, `stg_products`, `stg_payments`
3. Mart tables created: `dim_customers`, `dim_products`, `fct_orders`
4. All tests pass

**Expected final status:** `Run completed successfully` (green)

If any test fails, check the **Artifacts** tab → `run_results.json` for the exact
failing model and column name.

---

### D6. Verify column metadata in Unity Catalog

`persist_docs` pushes dbt YAML descriptions into Unity Catalog column metadata.
This is what makes the Act 4 Genie Space accurate — Genie reads UC comments, not
your local YAML files.

Run in the Databricks SQL Editor:
```sql
DESCRIBE TABLE EXTENDED enablement.ecommerce.dim_customers;
```

Each column should have a **Comment** value. For example:

| col_name | data_type | comment |
|---|---|---|
| customer_id | int | Unique customer identifier. Primary key. |
| customer_segment | string | Derived value tier: high_value >= $500, mid_value >= $100, low_value < $100 |
| total_lifetime_value | decimal(38,18) | Sum of all successful payment amounts for this customer (USD). |

You can also verify in the UI: **Catalog** → `enablement` → `ecommerce` → `dim_customers` → **Columns** tab.

If comments are empty: verify `persist_docs` is in `platform/dbt_project.yml` under
the `marts:` config block, then re-run the job.

---

### D7. Create the consumer projects (Mesh)

The `marketing` and `finance` projects use cross-project refs like
`{{ ref('platform', 'fct_orders') }}`. In dbt Cloud, this resolves via the
**Project Dependencies** feature — the consumer project reads the platform project's
published metadata at compile time.

**Create the marketing project:**

1. **Account settings** → **Projects** → **New project**
2. Fill in:

| Field | Value |
|---|---|
| Project name | `marketing` |
| dbt version | `1.9` |
| Connection | `enablement-databricks` |
| Repository | Same repo |
| Project subdirectory | `marketing` |

3. Add an environment: **Deploy** → **Environments** → **New environment**
   - Name: `Production`
   - Schema: `ecommerce_marketing`

4. Set the project dependency:
   - In the `marketing` project → **Settings** → **Project dependencies**
   - Click **Add dependency** → select `platform`
   - This tells dbt Cloud: "when compiling `marketing`, fetch platform's published manifest"
   - Click **Save**

**Repeat for the finance project:**
- Project name: `finance`
- Subdirectory: `finance`
- Schema: `ecommerce_finance`
- Project dependency: `platform`

---

### D8. Create and run consumer jobs

For each consumer project, create a deploy job and run it.

**Marketing job:**
1. In the `marketing` project → **Deploy** → **Jobs** → **New job** → **Deploy job**
2. Job name: `marketing - full build`
3. Commands: `dbt deps`, `dbt build`
4. Click **Run now**

Expected: `mart_customer_segments` and `mart_country_performance` created in
`enablement.ecommerce_marketing`.

**Finance job:**
Same steps in the `finance` project.
Expected: `fct_revenue` and `fct_revenue_by_product` created in
`enablement.ecommerce_finance`.

> If a consumer job fails with "Cross-project ref 'platform.fct_orders' not found":
> the platform project's **Defer to** settings or published state is missing.
> Go to the platform project → **Deploy** → **Environments** → ensure the environment
> has **Generate docs on run** enabled, then re-run the platform job first.

---

### D9. Full build summary

After all three jobs complete, verify in the SQL Editor:

```sql
-- Platform marts
SHOW TABLES IN enablement.ecommerce;
-- Expected: dim_customers, dim_products, fct_orders (+ staging views)

-- Marketing consumer models
SHOW TABLES IN enablement.ecommerce_marketing;
-- Expected: mart_customer_segments, mart_country_performance

-- Finance consumer models
SHOW TABLES IN enablement.ecommerce_finance;
-- Expected: fct_revenue, fct_revenue_by_product
```

---

### D10. What dbt Mesh gives you — and what Lakeflow alone cannot

This is a key demo talking point. The three dbt Cloud projects are not just a
cleaner version of Lakeflow gold tables. They introduce a governance layer that
Lakeflow pipelines fundamentally cannot replicate without significant manual effort.

**Side-by-side: same outcome, very different cost**

| Capability | dbt Mesh (this repo) | Lakeflow-only equivalent |
|---|---|---|
| **Cross-team data contracts** | `contract: enforced: true` on mart models — if `platform` changes a column type or removes a column, the build fails immediately before any consumer is affected | No enforcement. A schema change in a Lakeflow gold table silently breaks downstream consumers at query time, not build time |
| **Access tiers (public vs protected)** | Staging models are `access: protected` — `marketing` and `finance` cannot reference them directly. Only `public` mart models are shared | In Lakeflow, you would need to manually manage UC `GRANT`/`REVOKE` permissions on each table for each team. No compile-time enforcement — a wrong ref compiles and fails only at runtime |
| **Cross-project refs with compile-time validation** | `{{ ref('platform', 'fct_orders') }}` is validated at compile time in dbt Cloud. If the model doesn't exist or is not public, the job fails before any SQL runs | A Lakeflow pipeline referencing another team's table uses a hardcoded string like `enablement.ecommerce_lakeflow.gold_fct_orders`. No validation until the pipeline runs |
| **Dependency graph across teams** | dbt Cloud shows the full lineage: `platform.fct_orders → marketing.mart_customer_segments`. Lineage is automatic, always up to date | Lakeflow shows lineage within a single pipeline. Cross-pipeline lineage requires Unity Catalog lineage (partial, table-level only) or manual documentation |
| **Shared test suite** | `dbt build` in `marketing` runs the marketing tests against the platform's public API. If platform breaks its contract, tests catch it | No equivalent. Each Lakeflow pipeline has its own `@dlt.expect` rules, defined manually, with no shared or inherited test logic |
| **Column metadata to Genie (automatic)** | `persist_docs: columns: true` pushes every column description from YAML into UC automatically on every run | Requires `COMMENT ON COLUMN` SQL statements for each column, maintained manually, with no link to the pipeline code |
| **Source freshness monitoring** | `dbt source freshness` checks all 5 raw sources in one command, with thresholds defined in code | No equivalent in Lakeflow. You would need to write a custom notebook or query to check `MAX(_loaded_at)` per table and alert manually |
| **Metric definitions (Semantic Layer)** | 12+ named metrics in `_semantic_models.yml` — `return_rate`, `revenue_per_customer`, etc. Consumed directly by Genie, BI tools, and dbt Cloud's Semantic Layer API | No equivalent. Metric logic lives inside SQL views or gold table transformations, duplicated across every consumer team that needs the same metric |

**The Lakeflow replication cost (rough estimate for this demo schema):**
- Contracts → ~50 manual `ALTER TABLE` + UC constraint statements, maintained by hand
- Access tiers → ~20 `GRANT`/`REVOKE` statements per new team onboarded
- Cross-pipeline lineage → a Unity Catalog lineage config or a manually maintained wiki
- Column metadata → ~80 `COMMENT ON COLUMN` statements, updated manually on every schema change
- Source freshness → a custom monitoring notebook + alerting workflow
- Shared metrics → metric logic duplicated in every team's gold table or BI layer

**The demo moment:** When you show `{{ ref('platform', 'fct_orders') }}` in the
`marketing` project and explain that dbt Cloud enforces this at compile time —
the question to ask the audience is: "How would you catch a breaking schema change
before it reaches your consumers if you were using Lakeflow alone?"

---

## Part E: Schedule the Data Generator (Source Freshness Demo)

This step schedules `03_data_generator.py` as a Databricks Workflow that runs
every 30 minutes, keeping most raw sources fresh while leaving `raw_payments`
intentionally stale. After 2 days, `dbt source freshness` will flag the payment
source — without anyone having to notice manually.

---

### E1. Upload the generator notebook

1. **Workspace** → navigate to your demo folder
2. **Import** → **File** → upload `databricks/notebooks/03_data_generator.py`

---

### E2. Create the Job

1. Left sidebar → **Jobs & Pipelines** → **Create** → **Job**
2. Give it a name: `ecommerce-data-generator`
3. Under **Tasks**, click **Add task** → **Notebook**
4. Fill in:

| Field | Value |
|---|---|
| Task name | `generate_fresh_data` |
| Type | Notebook |
| Source | Workspace |
| Path | Browse to the notebook you just uploaded |
| Cluster | Serverless (recommended) or any existing cluster |

5. Click **Create task**

---

### E3. Set the schedule

1. On the job detail page, click the **Schedules & Triggers** tab
2. Click **Add trigger**
3. Select **Scheduled**
4. Set the schedule to **Every 30 minutes**
   - In cron syntax: `0 0/30 * * * ?`
   - Or use the UI: Repeat every `30` Minutes
5. Timezone: set to your local timezone so runs are predictable
6. Click **Save**

---

### E4. Run it once manually to verify

Before relying on the schedule, trigger a manual run:

1. On the job detail page, click **Run now** (top right)
2. Wait for it to complete (< 1 minute with serverless)
3. Check the output — you should see:
   ```
   Step 1: Checking whether to add a new customer...
     (Inserted customer 11: Priya Sharma (IN))   ← may vary
   Step 2: Inserting 3 new orders...
     Order 1016: customer=3, status=completed, amount=$287.50, method=credit_card
     ...
   Step 3: Inserting order items...
     Inserted 7 order items across 3 orders.
   Step 4: raw_payments — SKIPPED (intentional).
   ```
4. The summary table at the end shows `last_loaded` timestamps.
   `raw_payments` will show the original seed timestamp — not today.

---

### E5. Verify source freshness with dbt

After the generator has run at least once, test the freshness check:

```bash
cd /Users/hichambabahmed/dbt-dbx-field-enablement/platform
dbt source freshness --profiles-dir .
```

**Same day as setup — expected output (all pass):**
```
Found 5 sources to check freshness for

raw_customers    [PASS]  Max loaded_at: just now (0 minutes ago)
raw_orders       [PASS]  Max loaded_at: just now (0 minutes ago)
raw_order_items  [PASS]  Max loaded_at: just now (0 minutes ago)
raw_products     [PASS]  Max loaded_at: just now (0 minutes ago)
raw_payments     [PASS]  Max loaded_at: just now (0 minutes ago)   ← seed timestamp
```

**After 1 day without re-seeding raw_payments:**
```
raw_payments     [WARN]  Max loaded_at: 1 day, 3 hours ago (warn_after: 1 day)
```

**After 2 days:**
```
raw_payments     [ERROR] Max loaded_at: 2 days, 1 hour ago (error_after: 2 days)
```

This is the demo moment. `raw_payments` goes stale automatically — you do nothing.
The Workflow keeps the other four sources green. dbt caught the silent failure.

---

### E6. Source freshness design summary (reference)

| Source | Generator updates it | Freshness thresholds | Why |
|---|---|---|---|
| `raw_customers` | Yes, every 30 min | warn 1h / error 6h | Simulates a live CRM feed |
| `raw_orders` | Yes, every 30 min | warn 1h / error 6h | Simulates a live order system |
| `raw_order_items` | Yes, every 30 min | warn 1h / error 6h | Same as orders |
| `raw_products` | No (static catalog) | warn 3d / error 7d | Product catalog rarely changes |
| `raw_payments` | **No — intentional** | **warn 1d / error 2d** | Simulates dead payment processor |

---

## Part F: Create Databricks Metric Views

This step creates 6 metric views in `enablement.ecommerce_metric_views` — the same
metrics as the dbt semantic layer, for the side-by-side comparison in Act of the demo
and Tab 3 of the Streamlit app.

---

### F1. Open the SQL Editor

1. Left sidebar → **SQL Editor**
2. Click **New query** (or open an existing editor tab)
3. Make sure the correct warehouse is selected in the warehouse dropdown (top right of editor)

---

### F2. Run the metric views script

1. Open `databricks/notebooks/02_metric_views.sql` in your local editor
2. Copy the entire file contents
3. Paste into the Databricks SQL Editor
4. Click **Run** (or Ctrl+Enter / Cmd+Enter)

The script creates:
- `enablement.ecommerce_metric_views` schema
- 6 individual metric views (`total_revenue`, `avg_order_value`, `total_orders`, `return_rate`, `customer_count`, `avg_lifetime_value`)
- 1 combined `all_metrics` view

The last statement is a verification query. Expected output:

| metric | value |
|---|---|
| total_revenue | 2157.99 (approximate) |
| avg_order_value | 239.78 (approximate) |
| total_orders | 15 |
| customer_count | 10 |
| avg_ltv | some positive number |

> If you get a permission error creating the schema, run:
> `GRANT CREATE SCHEMA ON CATALOG enablement TO \`your.email@company.com\`;`

---

## Part G: Create Genie Spaces

You need three Genie Spaces — one for each act of the demo. The contrast between
them is the central demo narrative.

---

### G1. Where to find Genie

1. Left sidebar → look for **AI/BI** section (may be labeled "Genie" in newer workspaces)
2. Click **Genie**
3. You will see a list of existing Genie Spaces (may be empty)
4. Click **New Genie Space** or **Create** (top right)

---

### G2. Create the Raw Tables Space (Act 1 — The Problem)

This space is intentionally minimal. The goal is to show Genie struggling.

1. Click **New Genie Space**
2. **Name:** `E-Commerce (Raw — Act 1)`
3. **Description:** `Raw tables — no column descriptions, no business rules` (optional)
4. In the **Tables** section, click **Add tables**:
   - Search for `enablement.ecommerce.raw_customers` → select it
   - Repeat for `raw_orders`, `raw_order_items`, `raw_products`, `raw_payments`
   - You should have exactly 5 tables selected
5. In the **Instructions** field, paste the following (copy from `databricks/genie/genie_raw_instructions.md` — the block under "Instructions"):

```
This is raw e-commerce data.

Tables:
- raw_customers: customer records
- raw_orders: order records
- raw_order_items: order line items
- raw_products: product catalog
- raw_payments: payment records

Revenue is in the amount column of raw_orders or the amount column of raw_payments.
```

6. Click **Save** (or **Create**)
7. Test with: *"What was total revenue last month?"* — confirm Genie answers ambiguously

---

### G3. Create the Lakeflow Gold Space (Act 3 — Better But Not Enough)

1. Click **New Genie Space**
2. **Name:** `E-Commerce (Lakeflow Gold — Act 3)`
3. **Tables** — add three gold layer tables:
   - `enablement.ecommerce_lakeflow.gold_dim_customers`
   - `enablement.ecommerce_lakeflow.gold_fct_orders`
   - `enablement.ecommerce_lakeflow.gold_fct_revenue`
4. **Instructions** — paste (from `databricks/genie/genie_lakeflow_instructions.md`):

```
E-commerce data from the Lakeflow gold layer.

Tables:
- gold_dim_customers: customers with lifetime value and segment.
  customer_segment values: high_value, mid_value, low_value.
  total_lifetime_value: sum of successful payments (USD).
- gold_fct_orders: orders with items and payment totals.
  status values: placed, shipped, completed, returned.
  amount_paid: USD amount paid for this order.
- gold_fct_revenue: daily revenue aggregates (completed orders only).
  daily_revenue: total revenue for the day.

Revenue = daily_revenue column in gold_fct_revenue (completed orders only).
High-value customer = total_lifetime_value >= 500.
```

5. Click **Save**
6. Test with: *"What was total revenue last month?"* — confirm Genie answers better
   but using the column name, not a structured definition

---

### G4. Create the dbt + Semantic Layer Space (Act 4 — The Solution)

This is the most important space. Take care to add the right tables only.

1. Click **New Genie Space**
2. **Name:** `E-Commerce Analytics (dbt + Semantic Layer — Act 4)`
3. **Tables** — add three dbt mart tables:
   - `enablement.ecommerce.dim_customers`
   - `enablement.ecommerce.dim_products`
   - `enablement.ecommerce.fct_orders`
   - **Do not add staging views** — only the mart tables
4. **Instructions** — paste the full block from `databricks/genie/genie_dbt_instructions.md`
   (the "Instructions" section — the long block starting with "This is a production
   e-commerce analytics database..."). This is ~40 lines.

5. Click **Save**

> Note: If your workspace supports the dbt Semantic Layer integration (dbt Cloud +
> Partner Connect), you can also connect the Semantic Layer here. That enables
> direct MetricFlow metric queries. For demo purposes, the instructions-based
> approach works without dbt Cloud.

---

### G5. Test all three Genie Spaces before the demo

Run these two queries on each space and confirm the expected contrast:

**Query 1:** *"What was total revenue last month?"*

| Space | What you want to see |
|---|---|
| Raw (Act 1) | Genie picks `amount` from either `raw_orders` or `raw_payments` — ambiguous or asks for clarification |
| Lakeflow (Act 3) | Genie uses `daily_revenue` from `gold_fct_revenue` — more confident, but column-name-driven |
| dbt (Act 4) | Genie uses `amount_paid WHERE status = 'completed'` — exact match to semantic layer definition |

**Query 2:** *"How many high-value customers do we have?"*

| Space | What you want to see |
|---|---|
| Raw (Act 1) | Genie can't answer — no `customer_segment` column in raw tables |
| Lakeflow (Act 3) | Genie answers — `customer_segment = 'high_value'` in gold table |
| dbt (Act 4) | Genie answers AND explains: "high_value is defined as total_lifetime_value >= $500, tested with accepted_values" |

If the dbt space gives obviously wrong answers, check:
- The instructions were fully pasted (they should be ~40 lines, not just 5)
- The right tables are added (mart tables only, not raw or staging)
- Column metadata is in UC (re-run `dbt build` if needed)

---

### G6. Pre-demo Genie warm-up

Genie performs better on familiar questions. Before a live demo, "warm up" each
space by running the demo queries once. This primes the Genie's context window
for the session and reduces latency on first answers.

Open all three spaces in separate browser tabs so you can switch between them instantly.

---

## Part H: Deploy the Streamlit App (Optional)

The Databricks App provides a 4-tab dashboard for demos where Genie is not the
primary focus, or as a backup if Genie is slow.

---

### H1. Update app.yml with your warehouse ID

Before deploying, edit `databricks/app/app.yml` and replace `YOUR_WAREHOUSE_ID`
with your actual warehouse ID (the hex string at the end of your HTTP path):

```yaml
# If your HTTP path is: /sql/1.0/warehouses/abc1234567890def
# Then warehouse ID is: abc1234567890def

env:
  - name: DATABRICKS_WAREHOUSE_ID
    value: "/sql/1.0/warehouses/abc1234567890def"   # replace this

resources:
  - name: dbt-dbx-enablement-warehouse
    sql_warehouse:
      id: abc1234567890def   # and this
```

---

### H2. Install the Databricks CLI (if not installed)

```bash
# macOS
brew install databricks/tap/databricks

# Or via pip
pip install databricks-cli

# Verify
databricks --version
```

Configure the CLI with your credentials:
```bash
databricks configure
# Enter:
#   Databricks Host: https://adb-xxxxxxxxxxxxxxxx.x.azuredatabricks.net
#   Token: dapi...
```

---

### H3. Deploy the app

```bash
cd /Users/hichambabahmed/dbt-dbx-field-enablement

databricks apps deploy dbt-dbx-enablement \
  --source-code-path ./databricks/app
```

If this is your first deploy, Databricks will create the app. Subsequent runs update it.

---

### H4. Alternatively: deploy manually via UI

1. Left sidebar → **Apps** (in the Compute section)
2. Click **Create app**
3. Name: `dbt-dbx-enablement`
4. Click **Create**
5. On the app detail page, click **Deploy** → upload the `databricks/app/` directory
6. Edit the `DATABRICKS_WAREHOUSE_ID` environment variable to match your warehouse

---

### H5. Verify all 4 tabs load

Once deployed (1–2 minutes), open the app URL and check:

| Tab | What to verify |
|---|---|
| Executive Dashboard | Revenue metric cards show dollar amounts, not 0 or errors |
| Semantic Layer Explorer | Selecting "Total Revenue" returns a bar chart by month |
| Metric Views vs dbt SL | Both columns show metric values; feature comparison table renders |
| Governance | "Public Models" count shows 3, contract table has 3 rows |

If a tab shows "Query error", the table it's querying doesn't exist yet — check
that the corresponding dbt project has been built.

---

## Pre-Demo Final Checklist

Run through this 10 minutes before going live:

- [ ] `enablement.ecommerce.raw_*` — 5 tables, data present
- [ ] Data generator job has run at least once (check last run time in Jobs & Pipelines)
- [ ] `dbt source freshness --profiles-dir .` — raw_customers/orders/items are PASS, raw_payments is WARN or ERROR
- [ ] `enablement.ecommerce_lakeflow.gold_*` — 3 gold tables present
- [ ] `enablement.ecommerce.dim_customers` — present and has column comments (DESCRIBE TABLE)
- [ ] `enablement.ecommerce.fct_orders` — present
- [ ] `enablement.ecommerce_metric_views.total_revenue` — returns a value
- [ ] Genie Space "Raw" — returns ambiguous answer to "what was total revenue?"
- [ ] Genie Space "Lakeflow" — returns cleaner answer to same question
- [ ] Genie Space "dbt" — returns accurate answer with status = 'completed' filter
- [ ] Browser tabs open: all 3 Genie Spaces, `_semantic_models.yml` in dbt Cloud IDE, dbt Cloud lineage graph
- [ ] dbt Cloud project dependency graph (platform → marketing + finance) ready to show
- [ ] `DEMO_SCRIPT.md` open in a second monitor or printed

---

## Troubleshooting

### dbt Cloud job fails: "Could not connect to Databricks"

1. In dbt Cloud → **Account settings** → **Connections** → `enablement-databricks`
2. Click **Test connection** — if it fails, the warehouse may have stopped
3. Go to Databricks → **SQL Warehouses** → verify the warehouse is **Running** (green dot)
4. If the warehouse was stopped, start it and re-run the dbt Cloud job

Also check that the PAT hasn't expired: Databricks → Settings → Developer → Access tokens.

---

### Cross-project ref fails in marketing or finance

**In dbt Cloud:** the consumer projects resolve `{{ ref('platform', 'fct_orders') }}`
by fetching the platform project's published state from dbt Cloud's metadata service.

Most common cause: the platform project's **Production environment** doesn't have
"Generate docs on run" enabled, so no published state exists.

Fix:
1. In the `platform` project → **Deploy** → **Environments** → `Production` → **Edit**
2. Check **Generate docs on run** → Save
3. Re-run the `platform - full build` job
4. Once it succeeds, re-run the marketing or finance job

---

### `persist_docs` didn't push column metadata to UC

Verify the setting is in `platform/dbt_project.yml`:
```yaml
models:
  platform:
    marts:
      +persist_docs:
        relation: true
        columns: true
```

If the setting is there but metadata is still missing, the job may need a
`--full-refresh` flag. In dbt Cloud → job → **Settings** → add `dbt run --full-refresh`
as a command, run once, then remove it.

After the run, check in SQL Editor:
```sql
DESCRIBE TABLE EXTENDED enablement.ecommerce.dim_customers;
-- Look for non-empty "comment" values in the column list
```

---

### Genie Space gives wrong or inconsistent answers

1. **Check instructions are complete** — the dbt Genie Space instructions should be
   ~40 lines. If you only pasted part of them, Genie won't have the business rules.

2. **Check the right tables are added** — the dbt space should have mart tables only:
   `dim_customers`, `dim_products`, `fct_orders`. Not raw tables, not staging views.

3. **Warm up the space** — run a simple query first ("how many customers?") before
   running complex queries during a demo.

4. **Use the fallback** — if Genie gives an unexpected answer during the demo,
   say: "Even when the AI gets it wrong, we have a ground truth. The definition
   is in the YAML. Let me show you." Then show `_semantic_models.yml`.

---

### Lakeflow pipeline failed

Most common causes:

1. **Raw tables don't exist** — run Part B first. The pipeline reads from `enablement.ecommerce.raw_*`.
2. **Permission denied on target schema** — your user needs `CREATE TABLE ON SCHEMA enablement.ecommerce_lakeflow`.
   Run: `GRANT CREATE TABLE ON SCHEMA enablement.ecommerce_lakeflow TO \`you@company.com\`;`
3. **Databricks Runtime too old** — DLT requires Runtime 11.3 LTS or later. Use the default cluster policy.

Check the pipeline error details in the DLT UI: click on the red node in the DAG
to see the specific error message.

---

### "Table not found" in the Streamlit app

The app queries tables that must exist before it can render:
- Tab 1 and 2: need `enablement.ecommerce.dim_customers`, `fct_orders`, `dim_products`
- Tab 3: also needs `enablement.ecommerce_metric_views.all_metrics`
- Tab 4: no live queries — renders static data

Build the platform project (Part D) and run Metric Views (Part F) before deploying the app.
