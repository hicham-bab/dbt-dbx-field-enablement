# FAQ — dbt + Databricks Field Enablement

Common questions from customers, champions, and Databricks SAs.
Each answer is designed to be honest, concise, and demo-backed.

---

## General Positioning

**Q: If we have Databricks, why do we need dbt?**

Databricks handles infrastructure: compute, storage, orchestration, and the lakehouse
platform. dbt handles the business transformation governance layer: version-controlled
SQL, tested metrics, documented columns, and the semantic layer that Genie reads.

They solve different problems. The customers who have both get: Databricks for data
movement and Lakeflow for ingestion; dbt for the business logic layer that non-engineers
can review and audit.

**Demo anchor:** Act 1 vs Act 4 — show what Genie answers look like before and after dbt.

---

**Q: Is dbt competing with Databricks Spark Declarative Pipelines (formerly DLT/Lakeflow)?**

No. Spark Declarative Pipelines (SDP) are a pipeline orchestration tool for
bronze/silver layers — ingestion, streaming, auto-lineage, Python-native transforms.
dbt operates on the gold/marts layer — SQL-based business logic, documentation,
testing, and the semantic layer. They are complementary by design.

The reference architecture: SDP Bronze/Silver → dbt Gold/Marts → Semantic Layer → Genie.

**Demo anchor:** Act 2 — architecture slide showing both in the same stack.

---

**Q: Does dbt work natively with Databricks?**

Yes. The `dbt-databricks` adapter is maintained by Databricks. dbt Fusion (the Rust
compiler in dbt 1.9+) was co-developed with Databricks for native performance.
Key integrations:
- `persist_docs` pushes column descriptions to Unity Catalog column metadata
- dbt models run as Databricks SQL queries
- dbt Cloud orchestrates on Databricks Workflows
- The Semantic Layer connects to Genie via the MetricFlow API

---

## Technical Questions

**Q: What is dbt Fusion and how is it different from dbt Core?**

dbt Fusion is a rewrite of the dbt compiler in Rust, introduced in dbt 1.9.
It is faster (10x+ for large projects), eliminates the Python runtime bottleneck,
and enforces stricter SQL syntax (no `::` casting, `arguments:` key on generic tests).

The models and YAML in this repo are Fusion-conformant — the Fusion compiler
runs inside dbt Cloud on every job execution. See `docs/fusion_cheat_sheet.md`
for the syntax rules that make this code Fusion-compatible.

---

**Q: What is dbt Mesh and why does it matter for Databricks customers?**

dbt Mesh is a multi-project architecture where a "platform" project exposes
public models (with contracts) that downstream "consumer" projects reference.
Breaking changes in the platform project cause consumer builds to fail — governance
enforced by the build system, not by process.

For Databricks customers: this replaces or complements cross-catalog data sharing
with a governance layer. Unity Catalog handles access control; dbt Mesh handles
breaking change detection and ownership declarations.

**Demo anchor:** Show `finance/models/fct_revenue.sql` using
`{{ ref('platform', 'fct_orders') }}` and the contract in `_marts.yml`.

---

**Q: What is the dbt Semantic Layer and how does it improve Genie?**

The dbt Semantic Layer (MetricFlow) lets you define named metrics in YAML:
```yaml
- name: total_recognised_revenue
  description: >
    Revenue from completed orders only. Canonical definition.
  type: simple
  type_params:
    measure:
      name: total_revenue
      filter: "{{ Dimension('order__status') }} = 'completed'"
```

Genie reads these definitions via Unity Catalog column metadata (pushed by `persist_docs`)
and via the Genie Space instructions (generated from `schema.yml`). The result:
Genie generates SQL that matches the business definition, not its best guess.

---

**Q: How does `persist_docs` work with Unity Catalog?**

When `persist_docs: relation: true, columns: true` is set in `dbt_project.yml`,
the `dbt-databricks` adapter pushes:
- Table-level descriptions → Unity Catalog table comments
- Column-level descriptions → Unity Catalog column comments

After `dbt run`, you can verify:
```sql
DESCRIBE TABLE enablement.ecommerce.dim_customers;
-- The "comment" column shows dbt descriptions from schema.yml
```

Genie reads these column comments natively. No manual copy-paste into Genie
Space instructions required for column-level context.

---

**Q: What is a dbt contract and why does it matter?**

A dbt contract (`contract: enforced: true`) in a model's YAML specifies the
expected schema: column names, data types, and constraints. When a downstream
project references this model with `{{ ref('platform', 'fct_orders') }}`,
dbt validates that the actual schema matches the declared contract at build time.

If the platform team removes a column or changes a data type, the consumer
project's `dbt build` fails — before the change reaches production.
This is the mechanism that makes dbt Mesh's governance real.

---

**Q: How does this demo run — dbt Cloud or local CLI?**

This demo runs on **dbt Cloud**. Three separate dbt Cloud projects (`platform`,
`marketing`, `finance`) are connected to the Databricks workspace. Each has its
own deploy job. The Fusion compiler (Rust-based, dbt 1.9+) runs inside dbt Cloud
on every job execution — you do not need a local dbt installation.

dbt Cloud adds on top of the Fusion compiler:
- Orchestration and scheduled jobs
- CI/CD environments (dev → staging → prod with slim CI)
- Project dependencies for Mesh cross-project refs
- The Semantic Layer API (queryable by Tableau, Looker, Genie, etc.)
- Auto-generated docs site from `schema.yml`

The `profiles.yml` files in each project subdirectory are kept for optional
local development but are not used by dbt Cloud jobs.

---

## Deployment Questions

**Q: Can we deploy dbt to Databricks using Asset Bundles instead of dbt Cloud?**

Yes. This repo includes a full Declarative Asset Bundle configuration
(`databricks.yml` + `resources/dbt_job.yml`) and a GitHub Actions CI/CD
pipeline (`.github/workflows/deploy-dbt.yml`). See `docs/dabs_cicd_guide.md`
for the complete guide.

Asset Bundles handle the deployment/execution layer: defining dbt jobs as
infrastructure-as-code, deploying to dev/prod targets, and triggering builds
from CI/CD. However, they deploy dbt Core on Databricks compute -- **not**
dbt Cloud. This means the Semantic Layer, Explorer, Mesh cross-project refs,
and Fusion compiler are not available.

For customers who need both IaC deployment and governance, the hybrid pattern
works: Asset Bundles manage the infrastructure, dbt Cloud manages the
governance layer. See `docs/dabs_cicd_guide.md` Part 8.

---

**Q: What are Declarative Asset Bundles? Are they different from Databricks Asset Bundles?**

Declarative Asset Bundles are the current evolution of Databricks Asset Bundles
(DABs). Same CLI (`databricks bundle`), same manifest format (`databricks.yml`),
but with enhanced capabilities: stateful deployments, drift detection,
incremental sync, and richer variable expressions.

The key improvement for dbt deployments: incremental sync means only changed
model files are uploaded on each `bundle deploy`, and `bundle validate` can
detect when workspace resources have drifted from your declared state.

See `docs/dabs_cicd_guide.md` Part 7 for the full comparison.

---

## Databricks Platform Questions

**Q: What's the git integration experience like on Databricks?**

Databricks has solid git integration via **Repos (Git Folders)**:
- Clone any GitHub, GitLab, Azure DevOps, or Bitbucket repo into the workspace
- Create branches, commit, push, and pull from the UI
- Edit `.py`, `.sql`, and `.yml` files directly in the workspace IDE
- Non-notebook files (YAML, configs) are visible and editable

**Where it gets friction-y:**
- Merge conflicts in notebooks can be painful — notebook cell markers create noisy diffs
- No built-in PR-triggered CI — you need GitHub Actions + Asset Bundles (1-2 days setup)
- No inline test results or lineage preview in the editor (dbt Cloud IDE has this)

**dbt Cloud comparison:** dbt Cloud IDE gives you a purpose-built editor with lineage preview,
inline test results, and automatic PR-triggered CI with isolated schemas. Both have git.
dbt Cloud has governance on top.

**Verdict:** Git integration is **not a gap** in Databricks. The developer experience for
governance workflows (PR → CI → isolated schema → test → merge) requires more setup
than dbt Cloud's built-in flow. See `PLATFORM_COMPARISON.md` Section 2.

---

**Q: Where do you see production code in Databricks? Is it mixed with exploratory work?**

Production code lives in the **Git repo** (GitHub/GitLab). In Databricks, you see it in:
1. **Repos/Git Folders** — clone the production branch into any workspace
2. **Jobs** — each production job references a specific repo + branch + commit
3. **Asset Bundles** — `databricks bundle deploy -t prod` deploys from repo to workspace

**The separation question:** By default, Databricks workspaces mix exploratory notebooks
with production pipelines in the same file tree. This is a **configuration gap**, not a
platform gap. Solutions (in order of effort):
- Folder naming conventions (`/Production/` vs `/Exploratory/`) — low effort, discipline-dependent
- Separate UC catalogs (`prod` vs `dev`) — medium effort, good data isolation
- Separate workspaces — higher effort, full isolation (common in enterprises)
- Asset Bundle targets (`dev` vs `prod`) — medium effort, code-driven

**dbt Cloud comparison:** dbt Cloud separates environments by default — dev, staging, prod
each with their own schema and credentials. Production code is inspectable in Explorer
with one click. No configuration needed.

**Verdict:** Databricks **can** separate production from exploratory, but it requires
intentional setup. dbt Cloud has it by default. See `PLATFORM_COMPARISON.md` Section 3.

---

**Q: Can Databricks instances communicate with each other?**

Yes, via two mechanisms:

**1. Delta Sharing** — share tables across workspaces, even across clouds (AWS, Azure, GCP).
The provider controls what's shared; the recipient queries shared tables as if local.
Works cross-cloud and even with non-Databricks recipients (any client that supports
the Delta Sharing protocol).

**2. Shared Unity Catalog metastore** — a single UC metastore can serve multiple workspaces.
All workspaces see the same catalogs, schemas, and tables. This is the simpler option
when workspaces are in the same cloud region.

**Effort:** Delta Sharing requires medium setup (create shares, manage recipients).
Shared metastore is lower effort but requires workspaces in the same region.

**dbt comparison:** dbt Mesh allows cross-project refs with contract enforcement
(`ref('other_project', 'model')`). This is a different layer — Delta Sharing shares
data, dbt Mesh shares governance. Both are needed in enterprise deployments.

**Verdict:** Cross-instance communication is **not a gap**. See `PLATFORM_COMPARISON.md` Section 8.

---

**Q: Can Databricks query external sources like Snowflake?**

Yes, via **Lakehouse Federation**. You can query Snowflake, PostgreSQL, MySQL,
SQL Server, BigQuery, Redshift, and any JDBC source as if they were local tables:

```sql
-- Create a connection to Snowflake
CREATE CONNECTION snowflake_conn
TYPE snowflake
OPTIONS (host 'account.snowflakecomputing.com', user 'svc', password secret('scope', 'key'));

-- Create a foreign catalog
CREATE FOREIGN CATALOG snowflake_data USING CONNECTION snowflake_conn;

-- Query it like a local table
SELECT * FROM snowflake_data.schema.table;
```

This is production-ready, low effort per connection. Federated tables appear in Unity
Catalog but don't have the same lineage depth as native Delta tables.

**dbt comparison:** dbt doesn't directly query across platforms in a single project. Each
dbt project targets one data platform. Cross-platform data movement happens at the
infrastructure layer (Lakehouse Federation, Fivetran, etc.), and dbt transforms the
result. The two are complementary.

**Verdict:** Cross-platform querying is **not a gap**. Databricks Lakehouse Federation
is genuinely good. See `PLATFORM_COMPARISON.md` Section 8.

---

## Competitive Questions

**Q: Databricks now has Metric Views — is the dbt Semantic Layer still relevant?**

Yes. See `METRIC_VIEWS_COMPARISON.md` for the full analysis. Short version:

Metric Views are sufficient for simple, stable metrics in Databricks-only environments.
The dbt Semantic Layer adds: PR-reviewed definitions, derived/ratio metric types,
multi-tool compatibility, data quality tests on underlying data, and a git audit trail.

The key question: "When a stakeholder asks 'who approved this revenue definition?',
what do you point to?" With Metric Views: the view DDL. With dbt: the PR history.

---

**Q: Can we use dbt with Databricks without dbt Cloud?**

Yes. The dbt Fusion CLI is free and open source. The `profiles.yml` files in each
project subdirectory support local execution — set `DBX_HOST`, `DBX_HTTP_PATH`,
and `DBX_TOKEN` as environment variables and run `dbt build --profiles-dir .`
from the project directory.

However, **dbt Mesh cross-project refs require dbt Cloud** (Team or Enterprise plan).
Without dbt Cloud, the `{{ ref('platform', 'fct_orders') }}` calls in the consumer
projects will fail because there is no shared metadata service to resolve them.
For demos where Mesh is the central story, dbt Cloud is required.

---

**Q: What does the setup actually look like? How long does it take?**

See `SETUP.md` for the full walkthrough. Short version:

1. Run `00_setup_raw_data.py` in Databricks — 5 raw Delta tables (5 min)
2. Run `01_lakeflow_pipeline.py` as a Spark Declarative Pipeline — 13 tables (10 min)
3. Connect dbt Cloud to Databricks, create 3 projects, run jobs (20 min)
4. Create 3 Genie Spaces (10 min)
5. Run the 5-act demo (25 min)

Total: ~55 minutes from zero to live demo.

---

**Q: Our customer is Databricks-native — they've never used dbt. Is this demo relevant?**

Yes — this is the most relevant demo for that customer. Show them:
- Act 1: what their current Genie experience probably looks like on raw/Lakeflow tables
- Act 4: what it looks like with dbt metadata
- The governance moment: `git log _semantic_models.yml`

The ask is not "replace Databricks with dbt" — it's "add the governance layer
that makes Databricks more valuable." Databricks-native customers have the most
to gain because they're building from scratch.
