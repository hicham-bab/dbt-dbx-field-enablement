---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
---

# Naming rules

Product names in this market changed three times in eighteen months. Getting one
wrong in front of a Databricks SA costs more credibility than the point you were
making was worth. CI enforces the banned strings below
(`.github/workflows/naming-lint.yml`).

## Scope: prose only

These rules apply to **prose**: docs, slide copy, demo narration, comments meant
for humans.

They do **not** apply to code identifiers: filenames, config keys, CLI commands,
API fields, package names, catalog and schema names. `databricks.yml`,
`databricks bundle deploy`, `01_lakeflow_pipeline.py` and
`materialized='metric_view'` are all correct as written. Never "fix" an
identifier to match a brand rule; matching the real name is always correct there.

## Databricks

| Don't write | Write | Why |
|---|---|---|
| Delta Live Tables, DLT | **Lakeflow pipelines** | Renamed. Only acceptable inside a "formerly Delta Live Tables" clause.[^lakeflow-pipelines-name] |
| Spark Declarative Pipelines (as the Databricks product) | **Lakeflow pipelines** | *Spark* Declarative Pipelines is the Apache Spark OSS framework Databricks donated the engine to. Lakeflow pipelines is the product that extends it.[^spark-declarative-pipelines-oss] |
| Lakeflow Declarative Pipelines | **Lakeflow pipelines** | Stale intermediate name. Current body copy drops "Declarative".[^lakeflow-pipelines-name] |
| SDP | **Lakeflow pipelines** | Acronym for a name that was never the product's. |
| Databricks Asset Bundles, DABs | **Declarative Automation Bundles** | Renamed March 2026.[^declarative-automation-bundles-name] The `databricks bundle` CLI is unchanged. |
| Declarative Asset Bundles | **Declarative Automation Bundles** | Never a real product name. Do not reintroduce. |
| Genie Space, Genie Spaces | **Genie Agents** | Genie is now One / Agents / Code.[^genie-agents-name] |

Genie, precisely: **Genie One** is the business-user interface, **Genie Agents**
are the domain environments data teams configure, **Genie Code** is the developer
assistant. When this repo says "build a Genie Agent on the dbt marts", that is
the Agents product.

## dbt

| Don't write | Write | Why |
|---|---|---|
| dbt Cloud | **dbt platform** | Only acceptable inside a "formerly dbt Cloud" clause. |
| dbt Explorer | **dbt Catalog**, or **Catalog** after first use | Renamed.[^dbt-catalog-name] |
| dbt platform IDE, dbt platform Studio, dbt Studio, Cloud IDE | **Studio IDE** | Pick one name; this is it. |
| DBT, Dbt | **dbt** | Always lowercase, even sentence-initial. |
| Coalesce (the conference) | - | Retired 31 January 2026. Note: `COALESCE()` in SQL is a function, not the conference, and is never a violation. |

**dbt Wizard and dbt Copilot are two different products.** Wizard is the agent
(public preview in Studio IDE; public beta in the Wizard home tab and the
terminal/CLI). Copilot is inline generation in Studio IDE and remains available
until Wizard reaches GA.[^dbt-wizard-vs-copilot] Do not use "dbt Wizard" as a
generic label for inline AI features.

Branded nouns keep their capitals: dbt Core, dbt Labs, Fusion, dbt Mesh, dbt
Catalog, dbt Wizard, Studio IDE, dbt Summit.

## Status words

Never write "GA" without checking. As of the `last_verified` date above:

- Fusion is the default engine on install and free to use, but the **Databricks
  adapter is Preview**, not GA. Same for Snowflake, BigQuery and Redshift; Spark
  and DuckDB are Beta.[^fusion-databricks-preview]
- Unity Catalog metric views are GA.[^metric-views-yaml]
- dbt Wizard is preview/beta depending on surface.[^dbt-wizard-vs-copilot]

## Adding a claim

Every competitive capability claim needs a footnote pointing at a claim ID in
`sources.yml`. If there is no source, either find one or cut the claim. See
`sources.yml` for the format.

[^lakeflow-pipelines-name]: https://docs.databricks.com/aws/en/ldp/concepts/where-is-dlt (retrieved 2026-08-11)
[^spark-declarative-pipelines-oss]: https://docs.databricks.com/aws/en/ldp/ (retrieved 2026-08-11)
[^declarative-automation-bundles-name]: https://docs.databricks.com/aws/en/dev-tools/bundles/ (retrieved 2026-08-11)
[^genie-agents-name]: https://docs.databricks.com/aws/en/genie/ (retrieved 2026-08-11)
[^dbt-catalog-name]: https://docs.getdbt.com/docs/explore/explore-projects (retrieved 2026-08-11)
[^dbt-wizard-vs-copilot]: https://docs.getdbt.com/docs/platform/wizard-overview (retrieved 2026-08-11)
[^fusion-databricks-preview]: https://docs.getdbt.com/docs/fusion/fusion-availability (retrieved 2026-08-11)
[^metric-views-yaml]: https://docs.databricks.com/aws/en/business-semantics/metric-views/ (retrieved 2026-08-11)
