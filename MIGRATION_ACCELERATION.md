# Faster Time to Value: Migrating Legacy → dbt + Databricks

How dbt (dbt Wizard + Fusion + Mesh) on Databricks compresses a legacy migration
from months to weeks — and lands **governed** models, not just lifted-and-shifted
SQL. Use this with customers who are already planning to move off a legacy stack.

> Framing note: the timelines below are directional and depend on scope. Lead with
> the *mechanism* (why it's faster), not a specific number. Confirm any customer-
> facing figures with PMM.

---

## The legacy starting points

Most Databricks migrations begin from one of these:

- **Stored procedures** — Oracle (PL/SQL), SQL Server (T-SQL), Teradata (BTEQ), Netezza
- **ETL tools** — Informatica PowerCenter, Talend, Matillion, DataStage
- **Hand-maintained warehouse SQL** — views, scripts, scheduled queries
- **Notebooks** — business logic embedded in ad-hoc Python/SQL

The shared problem: the logic is undocumented, untested, dialect-specific, and
scattered across tools. A pure lift-and-shift onto Databricks **moves the mess** —
it doesn't fix it, and the tech debt resurfaces the moment someone connects Genie.

---

## Why dbt + Databricks migrates faster

1. **dbt Wizard does the heavy lifting.** The terminal-native AI agent is grounded
   in the project's compiled state, lineage graph, and semantic definitions. It
   refactors legacy SQL / stored-proc logic into dbt models from natural language,
   generates the tests and documentation as it goes, shows a **reviewable diff**, and
   **validates each change against the warehouse** before you see it. It's
   impact-aware — it flags the downstream models, tests, and metrics a change affects.
   The Wizard CLI is **BYOK**: point it at the **Databricks Unity Catalog AI Gateway**
   (beta) — models served from the customer's *own* Databricks workspace — so the agent's
   LLM access, spend, and policy stay under the same Unity Catalog governance as their
   data. (Also supports OpenAI, Anthropic, Azure OpenAI, Bedrock, Gemini, and Snowflake
   Cortex.)

2. **Fusion catches dialect differences in real time.** Cross-dialect translation
   (Oracle / Teradata / T-SQL → Databricks SQL) is where migrations stall. Fusion's
   real-time compilation surfaces incompatible syntax and functions *as you type*
   (~30x faster parse/compile than dbt Core) — a tight feedback loop instead of
   discovering failures in an overnight batch run.

3. **Databricks Lakeflow lands the raw data.** Lakeflow Declarative Pipelines ingest
   source data into Unity Catalog; dbt takes it from bronze → governed marts. Native
   dbt task or the dbt platform task orchestrates the dbt side.

4. **You migrate *into* governance, not just onto a new platform.** Every migrated
   model arrives with dbt tests, an enforced contract, documentation persisted to
   Unity Catalog, column-level lineage, and — where wanted — a Semantic Layer metric
   or a Unity Catalog metric view (`materialized='metric_view'`). The migration *is*
   the governance rollout; you don't run a second project for it later.

---

## Time-to-value contrast

| Migration phase | Manual re-platform (lift & shift) | dbt + Databricks (Wizard + Fusion) |
|---|---|---|
| Understand legacy logic | Weeks of code archaeology | Wizard reads the code and maps lineage |
| Translate SQL dialect | Manual, error-prone, fails at runtime | Fusion flags dialect diffs at compile time |
| Add tests + docs | Deferred to "later" (i.e. never) | Generated during the migration |
| Land governed metrics | Separate project after go-live | Same motion — Semantic Layer / UC metric views |
| First trusted, auditable output | Months | Weeks |

---

## The one-line pitch

> "You're moving off [Informatica / Oracle / Teradata] anyway. Do it once and land on
> Databricks **already governed** — dbt Wizard and Fusion turn a months-long
> re-platform into a weeks-long migration that ships tested, documented,
> semantic-layer-ready models. Faster time to value, and you never pay down the tech
> debt later because it never accrues."

---

## How to demo it

1. Show a legacy artifact (a stored proc or an Informatica mapping export).
2. In the dbt CLI, ask **dbt Wizard** to convert it to a dbt model — point at the
   reviewable diff, the generated tests, and the description.
3. Let **Fusion** compile it live — show a dialect issue caught instantly.
4. Point at the target-state in this repo: `platform/` marts with contracts, the
   Semantic Layer, and `platform/models/metrics/orders_metric_view.sql` (a governed
   Unity Catalog metric view) — "this is what the migrated model looks like when it
   lands: governed, tested, and ready for Genie."

Related dbt Labs assets: the dbt Wizard migration workflows and the
"migrate a dbt project across platforms" guidance (Fusion real-time dialect checking).
