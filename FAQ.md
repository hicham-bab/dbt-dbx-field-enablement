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

**Q: The customer is migrating off a legacy stack (Informatica / Oracle / Teradata). How does dbt + Databricks speed that up?**

It turns a months-long re-platform into a weeks-long migration that lands *governed*
models. Three accelerators:
- **dbt Wizard** refactors legacy SQL and stored-proc logic into dbt models from
  natural language, generating tests and docs and validating each change against the
  warehouse before you see the diff.
- **Fusion** catches SQL-dialect differences (Oracle/Teradata → Databricks SQL) at
  compile time, in real time — where lift-and-shift projects usually stall.
- **Lakeflow** lands the raw data in Unity Catalog; dbt takes it to governed marts.

The key point: you migrate *into* governance (tests, contracts, docs, Semantic Layer /
UC metric views) rather than lifting-and-shifting the mess and paying the tech debt
later. See `MIGRATION_ACCELERATION.md` for the full narrative and demo flow.

---

**Q: Is dbt competing with Databricks Spark Declarative Pipelines (formerly Delta Live Tables)?**

No. Spark Declarative Pipelines (SDP) are a pipeline orchestration tool for
bronze/silver layers — ingestion, streaming, auto-lineage, Python-native transforms.
dbt operates on the gold/marts layer — SQL-based business logic, documentation,
testing, and the semantic layer. They are complementary by design.

The reference architecture: SDP Bronze/Silver → dbt Gold/Marts → Semantic Layer → Genie.

**Demo anchor:** Act 2 — architecture slide showing both in the same stack.

---

**Q: Does dbt work natively with Databricks?**

Yes. The `dbt-databricks` adapter is maintained by Databricks, and the dbt Fusion
engine is generally available for Databricks — with native OAuth, ADBC connectivity,
and parse/compile up to ~30x faster than dbt Core. Key integrations:
- `persist_docs` pushes column descriptions to Unity Catalog column metadata
- dbt models run as Databricks SQL queries
- dbt can author Unity Catalog metric views natively (`materialized='metric_view'`, dbt-databricks 1.12+)
- Orchestrate from either side: run dbt in a Lakeflow Jobs dbt task, or trigger a governed dbt platform job from Lakeflow via the dbt platform task
- The Semantic Layer connects to Genie and other BI tools via the MetricFlow API

---

## Technical Questions

**Q: What is dbt Fusion and how is it different from dbt Core?**

dbt Fusion is a ground-up rewrite of the dbt engine in Rust — a separate engine,
not a feature of a specific dbt version. It is generally available (including the
Databricks adapter), parses and compiles up to ~30x faster on Databricks, eliminates
the Python runtime bottleneck, and enforces stricter SQL syntax (no `::` casting,
`arguments:` key on generic tests). dbt Core v2.0 is the Apache-2.0 foundation it
builds on.

Fusion runs three ways: the free `dbt` CLI, the dbt VS Code extension (real-time
compilation and LSP), or the dbt platform. The models and YAML in this repo are
Fusion-conformant — see `docs/fusion_cheat_sheet.md` for the syntax rules that make
this code Fusion-compatible.

---

**Q: What is dbt Wizard, and how does it fit the agentic story Databricks is pushing?**

dbt Wizard is dbt's terminal-native AI agent for analytics engineering (public beta;
available to dbt platform *and* self-hosted users). It replaces the older inline dbt
Copilot experience. What makes it different from a generic coding assistant is that it
is **grounded in the dbt project's compiled state, lineage graph, and semantic
definitions** from the first prompt — it knows which models are healthy, what depends
on what, and where tests/docs are missing before it writes anything. It builds and
refactors from natural language, shows a reviewable diff, and **validates its own
changes against the warehouse** before you see them. It can also connect to MCP servers,
including the dbt MCP server, for Semantic Layer metadata and cross-project context.

Why this matters on Databricks: Summit 2026 was an agentic story — Agent Bricks (with
the Claude Code SDK), the Unity AI Gateway, and Genie Ontology. dbt Wizard is the
governed-development counterpart: agents that *build* trusted data models on the same
project state that Genie and Databricks agents *consume*. It's AND, not OR — governed
authoring (dbt Wizard) feeding governed consumption (Genie).

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

The dbt Semantic Layer (MetricFlow) lets you define named metrics in YAML. On the
latest spec (dbt Core 1.12+ / Fusion), a metric is configured directly on its model:
```yaml
metrics:
  - name: total_recognised_revenue
    description: >
      Revenue from completed orders only. Canonical definition.
    type: simple
    agg: sum
    expr: amount_paid
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

**Q: How does this demo run — dbt platform or local CLI?**

This demo runs on **dbt platform**. Four dbt platform projects (`platform`,
`marketing`, `finance`, `data_science`) are connected to the Databricks workspace.
Each has its own deploy job. The Fusion engine (Rust-based) runs on every job
execution — you do not need a local dbt installation.

dbt platform adds on top of the Fusion engine:
- Orchestration and scheduled jobs
- CI/CD environments (dev → staging → prod with slim CI)
- Project dependencies for Mesh cross-project refs
- The Semantic Layer API (queryable by Tableau, Looker, Genie, etc.)
- Auto-generated docs site from `schema.yml`

The `profiles.yml` files in each project subdirectory are kept for optional
local development but are not used by dbt platform jobs.

---

## Deployment Questions

**Q: Can we deploy dbt to Databricks using Asset Bundles instead of dbt platform?**

Yes. This repo includes a full Declarative Asset Bundle configuration
(`databricks.yml` + `resources/dbt_job.yml`) and a GitHub Actions CI/CD
pipeline (`.github/workflows/deploy-dbt.yml`). See `docs/dabs_cicd_guide.md`
for the complete guide.

Asset Bundles handle the deployment/execution layer: defining dbt jobs as
infrastructure-as-code, deploying to dev/prod targets, and triggering builds
from CI/CD. The dbt job runs the dbt CLI on Databricks compute (you can use the
Fusion engine here — it is free and open source). What Asset Bundles alone do
**not** give you are the dbt platform services layered on top: the hosted
Semantic Layer API, Explorer, hosted Mesh metadata for cross-project refs, and
managed orchestration with slim CI.

For customers who need both IaC deployment and governance, the hybrid pattern
works: Asset Bundles manage the infrastructure, dbt platform manages the
governance layer. See `docs/dabs_cicd_guide.md` Part 8.

---

**Q: The customer wants Databricks to be the orchestrator. Do they lose dbt governance?**

No — this is a false trade-off in 2026. Lakeflow Jobs has two native dbt integrations:

- **dbt task** — runs dbt Core on Databricks compute (serverless by default). Good
  for a single project with no Semantic Layer or Mesh needs.
- **dbt platform task** — triggers and monitors an existing **governed dbt platform
  job** from Lakeflow Jobs via the dbt platform API. The customer keeps Databricks
  as the single pane of glass *and* gets the Semantic Layer, Explorer, Mesh, slim
  CI, and Fusion. (Continuous triggers aren't supported for this task — schedule or
  event-trigger it.)

So "we orchestrate everything in Databricks" and "we want dbt governance" are no
longer mutually exclusive. Recommend the dbt platform task for
Databricks-orchestration-first teams.

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
- No inline test results or lineage preview in the editor (dbt platform IDE has this)

**dbt platform comparison:** dbt platform IDE gives you a purpose-built editor with lineage preview,
inline test results, and automatic PR-triggered CI with isolated schemas. Both have git.
dbt platform has governance on top.

**Verdict:** Git integration is **not a gap** in Databricks. The developer experience for
governance workflows (PR → CI → isolated schema → test → merge) requires more setup
than dbt platform's built-in flow. See `PLATFORM_COMPARISON.md` Section 2.

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

**dbt platform comparison:** dbt platform separates environments by default — dev, staging, prod
each with their own schema and credentials. Production code is inspectable in Explorer
with one click. No configuration needed.

**Verdict:** Databricks **can** separate production from exploratory, but it requires
intentional setup. dbt platform has it by default. See `PLATFORM_COMPARISON.md` Section 3.

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

Metric views are sufficient for simple, stable metrics in Databricks-only environments.
The dbt Semantic Layer adds: PR-reviewed definitions, derived/ratio metric types,
multi-tool compatibility, data quality tests on underlying data, and a git audit trail.

And it's not either/or: with dbt-databricks 1.12+, dbt can **author** Unity Catalog
metric views (`materialized='metric_view'`), so the customer's own metric views become
version-controlled, tested dbt models.

The key question: "When a stakeholder asks 'who approved this revenue definition?',
what do you point to?" With hand-authored metric views: the view DDL. With dbt: the PR history.

---

**Q: At Summit 2026 Databricks shipped Unity Catalog Metrics (GA), a Business Glossary, Domains, and Genie Ontology. Doesn't that replace the dbt Semantic Layer?**

No — those are complementary, and dbt is the governed source of truth that feeds them.
Databricks' own framing is useful here: **Genie Ontology is a *context layer* that
*consumes* a semantic layer** (Unity Catalog Metrics/Glossary) and enriches it with
relationships and usage signals. dbt sits underneath that:

- **dbt authors and governs UC Metrics** (`materialized='metric_view'`) — version control,
  tests, contracts, lineage, PR review — instead of hand-authoring them in the catalog.
- **The dbt Semantic Layer** provides the same governed definitions across the *whole*
  stack (Tableau, Power BI, Looker, Python, AI agents), not just Databricks tools.
  Databricks acknowledges the context an agent needs "also lives in dbt, Snowflake,
  Tableau…" — dbt is a first-class source of that governed context.
- **UC Glossary + Domains** capture business terms and organization; dbt's descriptions,
  groups, and `access:` tiers map cleanly to them and can be the reviewed, versioned
  origin of those definitions.

Net: Genie Ontology and UC Metrics get *better* when the semantic definitions feeding
them are governed in dbt. Position dbt as the definition source of truth, not a competitor
to the context layer. (Confirm the latest joint messaging with PMM.)

---

**Q: Can we use dbt with Databricks without dbt platform?**

Yes. The dbt Fusion CLI is free and open source. The `profiles.yml` files in each
project subdirectory support local execution — set `DBX_HOST`, `DBX_HTTP_PATH`,
and `DBX_TOKEN` as environment variables and run `dbt build --profiles-dir .`
from the project directory.

However, **dbt Mesh cross-project refs require dbt platform** (Team or Enterprise plan).
Without dbt platform, the `{{ ref('platform', 'fct_orders') }}` calls in the consumer
projects will fail because there is no shared metadata service to resolve them.
For demos where Mesh is the central story, dbt platform is required.

---

**Q: What does the setup actually look like? How long does it take?**

See `SETUP.md` for the full walkthrough. Short version:

1. Run `00_setup_raw_data.py` in Databricks — 6 raw Delta tables (5 min)
2. Run `01_lakeflow_pipeline.py` as a Spark Declarative Pipeline — 13 tables (10 min)
3. Connect dbt platform to Databricks, create 3 projects, run jobs (20 min)
4. Create 3 Genie Spaces (10 min)
5. Run the 5-act demo (25 min)

Total: ~55 minutes from zero to live demo.

---

**Q: Our customer is Databricks-native — they've never used dbt. Is this demo relevant?**

Yes — this is the most relevant demo for that customer. Show them:
- Act 1: what their current Genie experience probably looks like on raw/Lakeflow tables
- Act 4: what it looks like with dbt metadata
- The governance moment: `git log _marts.yml` (metric + contract history in one file)

The ask is not "replace Databricks with dbt" — it's "add the governance layer
that makes Databricks more valuable." Databricks-native customers have the most
to gain because they're building from scratch.
