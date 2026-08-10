---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
reverify: quarterly, and after every Databricks DBR / dbt platform release
---

# dbt + Databricks - competitive reference

**This is the prep doc, not the call doc.** Read it before a competitive
conversation; take `BATTLE_CARD.md` into the call itself.

It exists because the battle card used to be 1,400 lines and nobody opened it
under pressure. One artifact per moment:

| Moment | Artifact |
|---|---|
| Live call, objection lands | `BATTLE_CARD.md` (one page, generated) |
| Prepping a call | this file |
| Running the demo | `DEMO_SCRIPT.md` |
| Sending to a champion afterwards | `FAQ.md` |
| Deep dive on one topic | `PLATFORM_COMPARISON.md`, `METRIC_VIEWS_COMPARISON.md` |

**The rule that makes all of this credible:** separate a **real platform gap**
from **"they didn't configure it"**. If Databricks can do something with
reasonable configuration effort, say so. Never claim a gap that is just a setup
step. Conceding correctly is what buys you the room on the gaps that are real.

---

## Fast facts, with the detail the card leaves out

### Fusion status

The **Databricks adapter is in Preview**, not GA.[^fusion-databricks-preview]
Snowflake, BigQuery and Redshift are also Preview; Spark and DuckDB are Beta.
Fusion itself is the default engine on install and free to use, via the CLI, the
VS Code extension, or dbt platform. It is a Rust rewrite with ADBC connectivity
and native OAuth.

Lead with "Preview". A Databricks SA who has read the release notes will know,
and claiming GA costs you every other claim in the conversation.

### Fusion speed

The widely quoted **~30x faster parse/compile** is a dbt Labs benchmark. It is
**not** published on docs.getdbt.com.[^fusion-speed] Do not present it as a
documented figure.

What works better: run `dbt parse` on the customer's own project, timed, next to
their current dbt Core run. That number is theirs and unarguable, and it is
usually more persuasive than any benchmark.

### Semantic Layer

The Semantic Layer API (MetricFlow JDBC) is a **dbt platform service**. It is not
self-hostable. This matters when a customer says "we'll just use dbt Core": Core
gets them the transformation engine, not the governed-metrics endpoint that
Genie, BI tools and agents query.

### Unity Catalog metric views

**GA**,[^metric-views-yaml] and dbt can author them via
`materialized='metric_view'`, added in dbt-databricks 1.12.0 on 18 May
2026.[^dbt-databricks-metric-view] This reframes the conversation: it is not dbt
*versus* metric views, it is dbt *governing* the metric views the customer
already wants.

They support star, snowflake and one-to-many joins with multi-level
joins.[^metric-views-joins] Do not claim otherwise. Full treatment in
`METRIC_VIEWS_COMPARISON.md`.

### Orchestration - the two native dbt tasks

- **dbt task** = dbt Core on Databricks compute. Fine for a single project. No
  Semantic Layer, no Catalog, no managed environments or CI, no cross-project
  state.
- **dbt platform task** = triggers and monitors a governed dbt platform job from
  Lakeflow Jobs. Databricks stays the single pane of glass **and** you keep the
  Semantic Layer, Catalog, Mesh, slim CI and Fusion. Continuous triggers are
  unsupported, so schedule or event-trigger it.

At 4+ projects, native tasks mean hand-wiring job chains and passing
`manifest.json` between them. dbt platform resolves cross-project dependencies
and `state:modified+` automatically.

### Reverse ETL

No first-class native reverse ETL in Databricks; Fivetran Activations fills it.
Databricks ships fast in this area, so **verify with PMM** before leaning on it.

### dbt Wizard and dbt Copilot

Two distinct products.[^dbt-wizard-vs-copilot] **Wizard** is the agent: public
preview in Studio IDE, public beta in the Wizard home tab and the terminal/CLI.
**Copilot** is inline generation in Studio IDE and remains available until Wizard
reaches GA. Do not describe Copilot as retired, and do not use "Wizard" as a
generic label for inline AI.

---

## Business value and cost of delay

Reframe from *cost of adoption* to *cost of delay*, and build every number from
the customer's own inputs. If you cannot source a "% saved" or "$/hr" figure,
do not say it.

- **CI compute.** `dbt build --select state:modified+` rebuilds only changed
  models and their dependents instead of full refreshes. Savings scale with
  project size and DAG shape, so measure it live: run
  `dbt ls --select state:modified+` against their recent PRs. Lakeflow has no
  equivalent. Note that the saving is a property of *their* PR sizes, not a
  constant.
- **Time-to-trusted-data.** Governed marts plus a Semantic Layer stand up in
  about a day on dbt platform, versus weeks assembling environments, CI and
  hand-curated metric context natively.
- **Cost of wrong answers.** Every inconsistent Genie or BI number triggers an
  investigation. One governed definition removes the whole class of problem.
- **Revenue motion.** Governed data reaching Salesforce or Slack via Fivetran
  Activations turns governance into action.

**On engineering-time multiples:** there is no source for "10-20x", so don't say
it. Ask how many hours a month go into cross-project job wiring, documentation
upkeep, metric discrepancy investigations and CI/CD maintenance, and let them
produce the multiple.

---

## Fivetran + dbt - win the data layer, on the platform

| Layer | Databricks-native | Why Fivetran + dbt | Gap type |
|---|---|---|---|
| Ingest | Lakeflow Connect (focused connectors → Delta) | 700+ connectors with schema-drift handling; faster time to value | coverage |
| Managed open tables | Delta + Predictive Optimization; UC Iceberg maturing | MDLS dual Delta/Iceberg, Fivetran-maintained. **Iceberg-first win** | edge |
| Transform / govern | notebooks / Lakeflow pipelines | dbt: contracts, tests, Semantic Layer, Mesh | **real gap** |
| Activate | none first-class | Fivetran Activations (reverse ETL) | **real gap** |

Full narrative in `FIVETRAN_DBT_DATABRICKS.md`. **Verify the fast-moving
Databricks rows with PMM** before you lean on them: Lakeflow Connect coverage, UC
managed Iceberg, and any native reverse ETL all move quickly.

---

## Genie and AI trust

Genie and agents are only as good as the governed context beneath them. The dbt
Semantic Layer, metric views, and the open Agents Schema feed Genie and Genie
Ontology trustworthy definitions.

The pitch is **"make Genie trustworthy"**, never "replace Genie". Post-Summit
2026, Genie Ontology is a context layer that *consumes* the semantic layer, which
makes dbt the governed source that makes it work rather than a competitor to it.

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

`DEMO_SCRIPT.md` is the full runbook. The numbers the demo actually produces are
in the README and in `facts.yml`; quote those, not rounder-sounding ones.

---

## Guardrails

- Separate a **real gap** from "they didn't configure it".
- Every capability claim about Databricks carries a source in `sources.yml`. The
  citation is the weapon: "here is the Databricks page that says so" ends an
  argument; "dbt has better testing" starts one.
- Databricks ships fast on ingestion, Iceberg and AI context. Verify anything in
  those areas with PMM before you lean on it.
- No invented stats. Bring the customer's numbers.
- It is **AND, not OR**: win the data layer, on the Databricks platform.

---

<!-- BEGIN GENERATED SOURCES - edit sources.yml, then run scripts/build_citations.py -->

## Sources

Generated from `sources.yml`. Every claim about a competitor's capabilities cites one of these. Do not edit by hand.

[^dbt-databricks-metric-view]: https://github.com/databricks/dbt-databricks/blob/main/CHANGELOG.md (retrieved 2026-08-10)
[^dbt-wizard-vs-copilot]: https://docs.getdbt.com/docs/platform/wizard-overview (retrieved 2026-08-10)
[^fusion-databricks-preview]: https://docs.getdbt.com/docs/fusion/fusion-availability (retrieved 2026-08-10)
[^fusion-speed]: https://docs.getdbt.com/docs/fusion/about-fusion (retrieved 2026-08-10)
[^metric-views-joins]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/basic-modeling (retrieved 2026-08-10)
[^metric-views-yaml]: https://docs.databricks.com/aws/en/uc-semantics/metric-views (retrieved 2026-08-10)

<!-- END GENERATED SOURCES -->
