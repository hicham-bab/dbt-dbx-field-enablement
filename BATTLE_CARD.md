# dbt + Databricks - Field Battle Card

A concise, fact-checked card for SAs and AEs. No invented stats, no hype. Deeper
detail lives in the linked docs. Where a claim moves fast (Databricks ships quickly),
it's marked **[verify w/ PMM]**. For any business case, use the **customer's own
numbers** - never quote a benchmark you can't defend.

---

## Positioning in 30 seconds

Databricks is the platform: compute, storage, orchestration, and AI (Genie, agents)
on the lakehouse. **Fivetran + dbt** (one company since 2026-06-01) is the governed
data layer on top: **ingest → transform/govern → activate**. We don't replace
Databricks - we make its AI trustworthy and get its data to the business. **Win the
data layer; love the platform.**

The question that opens most deals:
> **"When Genie gives you a number, can you prove where it came from and who approved it?"**
> If the answer is no, that's your opening.

---

## Fast facts (mid-2026, verifiable)

- **Fusion is GA on Databricks** - Rust engine, ~30x faster parse/compile than dbt
  Core, ADBC connectivity, native OAuth. Runs free (CLI / VS Code) or in dbt platform.
- **The Semantic Layer API (MetricFlow JDBC) is a dbt platform service** - not
  self-hostable. It's the governed-metrics endpoint Genie, BI, and agents query.
- **Unity Catalog metric views are GA** - and dbt can author them
  (`materialized='metric_view'`, dbt-databricks 1.12+). Complementary, not competing.
- **Two native dbt tasks in Lakeflow Jobs:** the **dbt task** (runs dbt Core) and the
  **dbt platform task** (triggers a governed dbt platform job). Databricks can stay the
  orchestrator without giving up governance.
- **No first-class native reverse ETL in Databricks** - Fivetran Activations fills it. **[verify w/ PMM]**
- **Fivetran MDLS** lands sources as open Delta **and** Iceberg in Unity Catalog, fully
  Fivetran-maintained (compaction, dedup, schema drift).
- **dbt Wizard** - terminal-native AI agent grounded in compiled state, lineage, and
  semantics; BYOK incl. the Databricks Unity Catalog AI Gateway.

---

## Objection handling

| They say | 15-second response (fact) | Business value |
|---|---|---|
| "Databricks does everything." | It does compute, storage, orchestration, AI. Natively it does **not** enforce cross-team column contracts, serve a Semantic Layer API to Genie/BI, or do reverse ETL. | Wrong Genie numbers and manual metric upkeep cost more than a YAML file per model. |
| "Adding dbt = more cost/complexity." | dbt's cost is a YAML file per model. The cost of *not* having it: hand-maintained Genie context, duplicated metric definitions, wrong numbers in prod. | Faster time-to-trusted-data; fewer "which number is right?" fire drills. |
| "We want fewer vendors." | Fivetran + dbt is now **one company** covering ingest → transform → activate. | One relationship for the whole data layer vs stitching separate tools. |
| "Unity Catalog is our governance." | UC governs **access** (who reads what). dbt governs **meaning** (what 'revenue' is - tested, versioned, PR-reviewed). You need both. | Auditable definitions → trustworthy Genie and clean audits. |
| "Lakeflow/Workflows handle orchestration." | Lakeflow orchestrates **execution**; dbt orchestrates **dependencies with governance** (contracts, cross-project, `state:modified+`). The **dbt platform task** even lets Lakeflow trigger governed dbt jobs. | Rebuild only what changed → cheaper CI; single pane of glass if they want it. |
| "Notebooks cover our transforms." | Great for exploration, not production governance. A notebook can't enforce a contract, fail a consumer's CI on a schema change, or serve a named metric to Genie. | Fewer silent breakages; governed reuse across teams. |
| "We'll just use the native dbt task." | That's dbt **Core** on your compute - no Semantic Layer, Explorer, or managed CI. Use the **dbt platform task** to get those and keep Databricks orchestration. | Avoids a week-6 rebuild when Genie needs governed metrics. |
| "Metric views replace the Semantic Layer." | Metric views are named calculations in the catalog; the Semantic Layer is a governed, multi-tool metric contract - and dbt authors **both**. | One definition served to Genie, Tableau, Power BI, agents - no drift. |
| "Our team doesn't know dbt." | dbt Python models run your existing PySpark; the change is `dbt.ref()` instead of `spark.read.table()`. | Governance without a rewrite. |

---

## Business value & cost of delay

Reframe from *cost of adoption* to *cost of delay*. Use these levers **with the
customer's own numbers** - do not quote invented benchmarks:

- **CI compute.** `dbt build --select state:modified+` rebuilds only changed models and
  their dependents instead of full refreshes. Savings scale with project size and DAG
  shape - measure it live: run `dbt ls --select state:modified+` on their recent PRs.
  Lakeflow has no equivalent.
- **Time-to-trusted-data.** Governed marts + Semantic Layer stand up in about a day on
  dbt platform vs weeks assembling native environments, CI, and hand-curated metrics.
- **Cost of wrong answers.** Every inconsistent Genie/BI number triggers an
  investigation. One governed definition removes the whole class of problem.
- **Revenue motion (activation).** Governed data reaching Salesforce/Slack/etc. via
  Fivetran Activations turns governance into action - no native Databricks equivalent.

> Build the case from their model count, PR cadence, and warehouse rate. If you can't
> source a "% saved" or "$/hr" figure, don't say it.

---

## Competitive deep-dives

### Orchestration - the two native dbt tasks
- **dbt task** = dbt Core on Databricks compute. Fine for a single project; no Semantic
  Layer, Explorer, managed environments/CI, or cross-project state.
- **dbt platform task** = triggers and monitors a governed dbt platform job from Lakeflow
  Jobs - Databricks stays the single pane of glass **and** you get the Semantic Layer,
  Explorer, Mesh, slim CI, and Fusion. (Continuous triggers unsupported - schedule or
  event-trigger it.)
- At 4+ projects, native tasks mean hand-wiring job chains and passing `manifest.json`
  between them; dbt platform resolves cross-project dependencies and `state:modified+`
  automatically.

### Metric views + Semantic Layer (complementary)
- dbt authors UC metric views (`materialized='metric_view'`) → version-controlled,
  tested, lineage-tracked.
- The Semantic Layer serves the same governed metrics to **every** tool via one API,
  not just Databricks-native surfaces.
- Post-Summit-2026: **Genie Ontology is a context layer that consumes the semantic
  layer** - dbt is the governed source that makes it trustworthy. → `METRIC_VIEWS_COMPARISON.md`.

### Fivetran + dbt - win the data layer, on the platform
| Layer | Databricks-native | Why Fivetran + dbt | Gap type |
|---|---|---|---|
| Ingest | Lakeflow Connect (focused connectors → Delta) | 700+ connectors + schema-drift; faster TTV | coverage |
| Managed open tables | Delta + Predictive Optimization; UC Iceberg maturing | MDLS dual Delta/Iceberg, Fivetran-maintained - **Iceberg-first win** | edge |
| Transform / govern | notebooks / Lakeflow declarative | dbt: contracts, tests, Semantic Layer, Mesh | **real gap** |
| Activate | none first-class | Fivetran Activations (reverse ETL) | **real gap** |

→ `FIVETRAN_DBT_DATABRICKS.md`. **[verify fast-moving Databricks items w/ PMM]**

### Genie / AI trust
Genie and agents are only as good as the governed context beneath them. dbt's Semantic
Layer + metric views + the open **Agents Schema** feed Genie / Genie Ontology
trustworthy definitions. The pitch is "make Genie trustworthy," not "replace Genie."

---

## Discovery questions (sharp, honest)

- "When Genie returns a number, can you show who approved that definition and when?"
- "If a platform team renames a column, what breaks - and do you find out in CI or in production?"
- "Does 'revenue' mean the same thing in Genie, Tableau, and the CFO's board deck?"
- "How does a governed metric get into Salesforce or Slack today?"
- "Are you Delta-only, or do you want an open Iceberg lakehouse?"

---

## Demo proof map

| Point to prove | Where |
|---|---|
| Governed, auditable Genie answers | Acts 1 → 4; Act 4c "60-second audit" |
| Cross-project governance (Mesh) | Act 4c |
| Fusion speed + state-aware CI | Act 4e |
| Python / DS governance | Act 4f |
| Bare dbt task vs dbt platform | Act 4g |
| Fivetran ingest (MDLS / Iceberg) | Act 0 |
| Activation to Slack | Act 4h |

See `DEMO_SCRIPT.md` for the full runbook.

---

## Guardrails - stay credible

- Separate a **real gap** from "they didn't configure it" (`PLATFORM_COMPARISON.md`).
- Databricks ships fast on ingestion, Iceberg, and AI context - **verify** Lakeflow
  Connect coverage, UC managed Iceberg, and any native reverse ETL with PMM before you
  lean on them.
- No invented stats. Bring the customer's numbers.
- It's **AND, not OR**: win the data layer, on the Databricks platform.
