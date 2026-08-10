---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
reverify: quarterly
---

# Databricks Metric Views + dbt: Governing Your Metrics

An honest guide for dbt field teams on how dbt and Databricks metric views fit
together. It answers the two questions customers ask: "Our customer already has
Databricks metric views - where does dbt fit?" and "dbt Semantic Layer or Unity
Catalog metric views?"

**Short answer (2026): it's AND, not OR.**

- As of **dbt-databricks 1.12.0** (18 May 2026), dbt can **author and govern Unity
  Catalog metric views directly** (`materialized='metric_view'`).[^dbt-databricks-metric-view]
  The customer's own metric views become version-controlled, tested, PR-reviewed
  dbt models.
- The **dbt Semantic Layer** serves governed metrics to *any* BI tool - not just
  Databricks - through one API.

So the real question is not "metric views or dbt." It's "which **serving surface**
do you need (Unity Catalog metric views for Databricks-native tools; the Semantic
Layer API for a multi-tool stack), and who governs the definitions upstream?"
Either way, **dbt is the authoring and governance layer.**

---

## Part 1: What Are These Two Things?

### Databricks Metric Views

Databricks metric views (GA April 2026, per the Databricks launch blog rather than
a docs page - treat the date as approximate; the implementation is being
open-sourced into Apache Spark) are YAML-defined metric objects saved to Unity
Catalog.[^metric-views-yaml] They
define measures, dimensions, and display formatting. They appear as first-class
objects in Genie and the SQL editor.

Example (from `databricks/notebooks/02a_metric_view_orders.yml`):

```yaml
version: 1.1
source: enablement.ecommerce.fct_orders

measures:
  - name: total_revenue
    expr: SUM(CASE WHEN status = 'completed' THEN amount_paid ELSE 0 END)
    display_name: Total Revenue
    comment: Sum of amount_paid for completed orders only.
    format:
      type: currency
      currency_code: USD
```

**What you get:** A named metric in Unity Catalog. Genie can query it. The SQL
editor can use it. The definition lives in the catalog, not in code.

### dbt Semantic Layer (MetricFlow)

The dbt Semantic Layer uses MetricFlow to define semantic models (entities,
dimensions) and named metrics. On the latest spec (dbt Core 1.12+ / Fusion),
this is configured as metadata on the dbt model itself, in Git. Metrics are
served via the Semantic Layer API (MetricFlow JDBC), queryable by Genie, Tableau,
PowerBI, Python SDK, and MCP-connected AI agents.

Example (a metric defined on the `fct_orders` model in `platform/models/marts/_marts.yml`):

```yaml
metrics:
  - name: total_recognised_revenue
    label: "Total Recognised Revenue (USD)"
    description: >
      Revenue from completed orders only. This is the canonical definition
      of recognised revenue for this business. Genie uses this when a user
      asks about "revenue" without further qualification.
    type: simple
    agg: sum
    expr: amount_paid
    filter: "{{ Dimension('order__status') }} = 'completed'"
```

**What you get:** A named, tested, version-controlled, PR-reviewed metric
definition that is served to every BI tool and AI agent via a single API.

---

## Part 1.5: dbt Can Author Your Databricks Metric Views (`materialized='metric_view'`)

This is the 2026 update that reframes the whole conversation. With
**dbt-databricks 1.12.0+**,[^dbt-databricks-metric-view] a Unity Catalog metric view can be a **dbt model**: set
`materialized='metric_view'` and put the metric-view YAML in the model body. dbt
deploys it to Unity Catalog like any other object.

```sql
-- platform/models/metrics/orders_metric_view.sql
{{ config(materialized='metric_view') }}
version: 1.1
source: {{ ref('fct_orders') }}
measures:
  - name: total_revenue
    expr: SUM(CASE WHEN status = 'completed' THEN amount_paid ELSE 0 END)
    display_name: Total Revenue
```

That means the customer's own Unity Catalog metric views - the ones Genie and
Databricks SQL already use - become:

- **Version-controlled** - every definition change is a commit and a PR
- **Tested** - the underlying mart carries dbt tests and an enforced contract
- **Lineage-tracked** - `ref('fct_orders')` wires the metric view into the dbt DAG
- **CI/CD-deployed** - promoted dev → prod through the same pipeline as every model

So the governance story below is no longer dbt *versus* metric views - it's dbt
*governing* the metric views the customer already wants. A working example lives
in `platform/models/metrics/` in this repo.

This matters more after Summit 2026: Unity Catalog Metrics went GA and Databricks
introduced **Genie Ontology**, a *context layer* that *consumes* the semantic layer
(UC Metrics/Glossary) to ground Genie. The better those definitions are governed, the
better Genie performs - and dbt is the version-controlled, tested, multi-platform
source those definitions can come from. dbt authors the UC metric views *and* serves
the same governed definitions to every non-Databricks tool.

---

## Part 2: The Feature Comparison

This compares the two **serving surfaces** at their common defaults: a metric
view hand-authored in the catalog vs a dbt Semantic Layer metric. Keep Part 1.5
in mind - dbt can now author the left column too, in which case the "version
control", "tests", and "lineage" rows apply to metric views as well. Choose the
serving surface by *where* the metrics are consumed; govern *both* with dbt
upstream.

> **Read this before you use the table in front of a customer.** Apply the same
> rule as `PLATFORM_COMPARISON.md`: separate a **real platform gap** from
> "they didn't configure it". Most of the left column is the second kind. A
> Databricks SA will correct you within a minute if you say metric views can't
> join, aren't version-controllable, or can't be reached outside Databricks -
> all three are false, and getting corrected on those costs you the rows that
> are actually true. The defensible gaps are narrow and they are enough:
> **no vendor-neutral metrics API**, **no cross-project metric contracts**, and
> **governance that is optional rather than structural** (you *can* put metric
> view YAML in git; nothing makes you, and the UI path leaves no history).

| Feature | Databricks Metric Views (hand-authored) | dbt Semantic Layer (MetricFlow) |
|---|---|---|
| **Definition format** | YAML saved to Unity Catalog | YAML in Git, next to dbt models |
| **Version control** | Possible but not inherent - the YAML can live in git and deploy via Declarative Automation Bundles;[^metric-views-yaml] hand-authored in the Catalog Explorer UI, it has no git history | Yes - the definition only exists in git, so there is no un-versioned path |
| **PR review process** | None built-in | Yes - YAML + SQL in same PR, reviewed by data team |
| **Audit trail** | UC audit log (who modified the object) | `git log` (who changed what, when, why, PR link) |
| **Human-readable description** | `comment` field (optional) | `description` + `label` fields (fed to Genie) |
| **Metric types** | Measures only (aggregation expressions) | Simple, derived, ratio, cumulative, conversion |
| **Derived metrics** | Manual SQL expression | `derived` type - explicit formula referencing other metrics |
| **Ratio metrics** | Manual SQL division | `ratio` type - numerator/denominator declared separately |
| **Time grain handling** | Manual DATE_TRUNC in expr | MetricFlow handles `time_granularity` natively |
| **Dimension slicing** | Dimensions in same YAML | Entities + dimensions across semantic models (joins handled) |
| **Cross-model joins** | Supported - star and snowflake schemas with multi-level joins, plus one-to-many[^metric-views-joins] | Entity relationships - MetricFlow resolves joins automatically |
| **Data quality tests** | None on metric definitions | dbt tests on underlying marts (`not_null`, `accepted_values`, custom) |
| **Column contracts** | None | `contract: enforced: true` - schema changes fail CI |
| **Multi-tool compatibility** | Reachable from anything that speaks JDBC/ODBC to Databricks SQL, since a metric view is a UC object. What's missing is a vendor-neutral *metrics* API, so BI tools consume it as a table, not as governed metrics | Any BI tool via Semantic Layer JDBC (Tableau, PowerBI, Looker, Genie) as first-class metrics |
| **AI agent access** | Any agent that can query Databricks SQL; Genie is the native surface | dbt MCP server - any AI agent can query metrics by name, across platforms |
| **Cross-project (Mesh)** | Not supported | Yes - metrics from platform consumed by all downstream projects |
| **Governance (access control)** | UC permissions on the metric view | `access:` + `groups:` + UC permissions + contracts |
| **Breaking change detection** | None - metric silently breaks if source changes | `dbt build` fails if contract violated; downstream consumers fail in CI |
| **Lineage** | UC captures lineage down to the column level,[^uc-column-level-lineage] but it is runtime-observed: only what actually ran, only when source and target are referenced by table name, and system tables keep a rolling 1-year window[^uc-lineage-retention] | dbt Catalog - column-level lineage derived from the code, so it exists before anything runs |
| **"Where does this number come from?"** | Read the SQL expression | Catalog → click metric → see full DAG from raw to metric |

---

## Part 3: The Big Narrative - Why This Distinction Matters

### 3.1 The Genie Trust Problem

Every Databricks customer deploying Genie faces the same fundamental question:
**"Can I trust this number?"**

When a business user asks Genie "what was total revenue last month?", Genie
generates SQL and returns a number. The user sees the number. They don't see:
- Which table it came from
- Which column was summed
- Whether returned orders were included or excluded
- Whether the definition matches the one Finance uses in their dashboard
- Whether anyone reviewed or approved this definition
- Whether the underlying data was tested for quality

This is not a Genie problem. It's a **metadata problem**. Genie can only be as
trustworthy as the definitions it's given.

Metric Views partially solve this: they give Genie a named metric with a
`comment` field. But they don't answer the trust question fully because they
lack the governance layer - version control, PR review, tests, contracts, and
traceable lineage from metric to raw source.

The dbt Semantic Layer solves the trust problem end-to-end:

```
Raw source → dbt staging (tested) → dbt mart (contracted) → Semantic model → Named metric
     ↑              ↑                      ↑                      ↑              ↑
  source freshness  schema tests      column contracts     entity joins    PR-reviewed definition
                                      access: public       grain declared  git log audit trail
```

Every layer is tested, documented, and version-controlled. When a business user
asks "can I trust this number?", the answer is not "I think so" - it's
"here's the PR that approved the definition, here's the test that validates the
data, and here's the lineage from raw to metric."

### 3.2 The Auditability Gap

This is the single most important distinction between Metric Views and the
dbt Semantic Layer. It's the argument that closes deals in regulated industries,
large enterprises, and any company where a CFO or auditor asks questions.

**The audit question:** "Who approved the revenue definition, and when did it
last change?"

**Metric Views answer:**
- Check Unity Catalog audit logs → shows the timestamp of the last modification
  and the identity of the modifier
- No commit message, no PR link, no review record
- No way to see what changed - only that something changed
- No way to see why - the business context behind the change is lost
- The `comment` field can be updated without any review process

**dbt Semantic Layer answer:** run it live, against this repo, and you get real
history rather than a screenshot:

```bash
$ git log --oneline platform/models/marts/_marts.yml
68b7194  Remove em dashes across all docs and repo text
e092d44  Refresh dbt + Databricks enablement for mid-2026
5663f96  Fix contract types: bigint for counts, decimal(18,2) for monetary columns
457e695  Fix Fusion YAML: move access/group/freshness into config blocks
7836e3d  Add all enablement files
```

Note **which file** you run this against. Simple metrics live on their model in
`platform/models/marts/_marts.yml`; the cross-model ratio and derived metrics
(`return_rate`, `revenue_per_customer`) live in
`platform/models/semantic/_semantic_models.yml`. Both are governed the same way,
but pointing at the wrong file in front of a customer undercuts the whole point.

- Every change has a commit hash, an author, a date, and a PR number
- The PR contains the discussion: why was the change made, who reviewed it,
  what tests were added
- The diff shows exactly what changed: "filter added: status = 'completed'"
- The full history is immutable and traceable

**Why this matters for Genie:**

When Genie returns a revenue number that doesn't match a dashboard, the
investigation path is completely different. **This is the canonical audit-question
table for this repo** - other docs link here rather than restating it:

| Step | Metric Views | dbt Semantic Layer |
|---|---|---|
| 1. "What definition did Genie use?" | Read the metric view SQL expression | Click metric in Catalog → see definition + description |
| 2. "Is this the right definition?" | Ask whoever created it, unless they put the YAML in git | Check the PR that approved it - reviewer names are on record |
| 3. "When did it last change?" | UC audit log - timestamp only | `git log` - timestamp + author + PR + commit message |
| 4. "What changed?" | Nothing to diff, *if* it was authored in the UI. If the YAML is in git, same as the right-hand column | `git diff` between any two commits |
| 5. "Where does the data come from?" | Read the `source:` field - one table reference | Catalog column-level lineage → full DAG from raw to metric |
| 6. "Is the underlying data correct?" | Run a manual query | dbt tests already validated it - check test results in Catalog |
| 7. "Can I prevent this from happening again?" | Add a comment and hope | Add a dbt test, enforce a contract, require PR review |

### 3.3 The "Where Does Genie's Answer Come From?" Workflow

This is the demo moment that resonates most with governance-conscious customers.
It answers the question every data leader eventually asks: **"I got a number from
Genie - show me exactly where it came from."**

**Step 1: Genie returns a number**

User asks: "What is our total recognised revenue?"
Genie returns: $14,364.45

> **Numbers in this walkthrough are the real ones this repo produces**
> ($14,364.45 across 52 completed orders in the seeded dataset). Ask for the
> all-time figure rather than "last month": monthly totals here are only a few
> hundred dollars and shift as the data generator runs, so a hardcoded monthly
> number on a slide will not match what Genie says on the day. Re-check with
> `dbt sl query --metrics total_recognised_revenue` before you present.

**Step 2: Trace the metric definition**

Open dbt Catalog → search "total_recognised_revenue" → click:

```
Metric: total_recognised_revenue
Label: "Total Recognised Revenue (USD)"
Description: Revenue from completed orders only. This is the canonical
             definition of recognised revenue for this business.
Type: simple
Measure: total_revenue
Filter: status = 'completed'
```

**Say:** "This is the definition Genie used. It's not a guess - it's a named
metric with an explicit filter. Revenue = completed orders only."

**Step 3: Trace the measure to the mart**

Click "total_revenue" measure → navigate to the semantic model → click the
underlying model: `fct_orders`

```
Model: fct_orders
Access: public
Contract: enforced
Column: amount_paid - "Total amount successfully paid for this order (USD).
         Counts only payments with status = 'success'."
```

**Say:** "The measure sums `amount_paid` from `fct_orders`. The column has a
contract - it must be `decimal(18,2)` and not null. If anyone changes the type,
every downstream consumer's build fails."

**Step 4: Trace the mart to the source**

Click column-level lineage for `amount_paid`:

```
fct_orders.amount_paid
  ← int_order_items_enriched (ephemeral)
    ← stg_payments.amount (staging view)
      ← raw_payments.amount (raw source)
```

**Say:** "Column-level lineage. From the metric all the way to the raw table.
Every hop is a dbt model - tested, documented, version-controlled. You can see
the full path from Genie's answer to the source table."

**Step 5: Verify data quality**

In Catalog, check the data health tile for `fct_orders`:

```
Tests: 7 passing
  ✓ not_null: order_id
  ✓ unique: order_id
  ✓ not_null: amount_paid
  ✓ not_null: order_date
  ✓ accepted_values: status [placed, shipped, completed, returned]
  ✓ relationships: customer_id → dim_customers
  ✓ assert_positive_revenue (custom)
```

**Say:** "Seven tests validated this data on the last run. The custom test
`assert_positive_revenue` ensures no negative amounts. The `accepted_values`
test ensures `status` can only be one of four values - the same values the
metric filter uses. If bad data enters, the tests catch it before Genie sees it."

**Step 6: Audit the definition history**

```bash
$ git log --oneline platform/models/marts/_marts.yml
68b7194  Remove em dashes across all docs and repo text
```

**Say:** "Every line is a commit with an author and a date. On your repo each one
also carries the PR number and the reviewer, so when the auditor asks 'who approved
this definition?' you have a name, a date, and the discussion thread - not a
timestamp on a catalog object."

**The contrast - try this with Metric Views:**

> "Now try the same workflow with a Metric View. Step 1: Genie returns a number.
> Step 2: Find the metric view in the catalog, read the SQL expression. Step 3:
> The `source` field says `fct_orders`. How was `fct_orders` built? Read the
> notebook. Step 4: What tests validate the data? There are none on the metric
> view - you'd need to check the notebook's Lakeflow expectations, if they exist.
> Step 5: Who approved this definition? Check the UC audit log - it shows a
> timestamp and a user ID, but not the rationale, the discussion, or the review."

### 3.4 The "Define Once, Serve Everywhere" Principle

This is the architectural argument that resonates with engineering leaders.

**Metric Views serve one ecosystem:** Databricks Genie and Databricks SQL.
If you also use Tableau, PowerBI, Looker, or a Python notebook - each tool
gets its own metric definition. You now have N definitions of "revenue" that
can drift independently.

**The dbt Semantic Layer serves every tool from one definition:**

```
                                  ┌─── Genie (via JDBC)
                                  │
_semantic_models.yml ──► JDBC ────┼─── Tableau
  (one definition)     endpoint   ├─── PowerBI
                                  ├─── Looker
                                  ├─── Python SDK (dbt-sl-sdk)
                                  ├─── AI agents (dbt MCP server)
                                  └─── Any tool that speaks JDBC
```

One YAML file. One PR review. One definition. Every tool gets the same number.

**The practical impact:**

| Scenario | Metric Views | dbt Semantic Layer |
|---|---|---|
| Finance asks Genie: "total revenue?" | Returns $14,364.45 (from metric view) | Returns $14,364.45 (from Semantic Layer) |
| Analyst queries Tableau: "total revenue?" | Returns $16,087.93 - quietly includes returned and shipped orders | Returns $14,364.45 (same definition via JDBC) |
| DS team queries Python: "total revenue?" | Returns $14,947.93 - forgot the `payment_status = 'success'` filter | Returns $14,364.45 (same definition via `dbt-sl-sdk`) |
| **CFO sees three different numbers** | "Which one is right?" | Doesn't happen - all three are the same |

This is the **single source of truth** problem. Metric Views solve it for
Databricks tools. The dbt Semantic Layer solves it for the entire stack.

### 3.5 The Governance Stack: What Each Layer Provides

The dbt Semantic Layer is not just a metric definition tool. It sits on top of
a governance stack that Metric Views don't have:

```
Layer 6: Named Metrics         → "total_recognised_revenue" queryable by name
Layer 5: Semantic Models       → Entities, dimensions, measures - grain declared
Layer 4: Column Contracts      → Schema enforced, types guaranteed, changes fail CI
Layer 3: dbt Tests             → not_null, unique, accepted_values, relationships, custom
Layer 2: Documentation         → Column descriptions pushed to UC via persist_docs
Layer 1: Version Control       → Git history, PR review, audit trail
Layer 0: dbt Models            → Tested SQL/Python transformations

Metric Views provide: Layer 6 only.
dbt Semantic Layer provides: Layers 0–6 as an integrated stack.
```

When a customer asks "why not just use Metric Views?", the answer is:
Metric Views give you the top layer. dbt gives you the full stack underneath.
Without Layers 1–5, Layer 6 is a named metric built on ungoverned foundations.

---

## Part 4: Where Metric Views Are the Right Serving Surface

Be honest. Unity Catalog metric views are the right serving surface when - and
remember dbt can still author and govern them via `materialized='metric_view'`
(Part 1.5), so this is about *where metrics are served*, not whether dbt is
involved:

1. **Simple, stable metrics** - fewer than 10 metrics, rarely change, no complex
   filters or time-grain requirements
2. **Databricks-only environment** - all BI consumers use Databricks SQL or Genie,
   no Tableau/PowerBI/Looker integration needed
3. **Small team, low governance overhead** - one person owns the metrics, manual
   sync is manageable
4. **Exploratory / prototype stage** - trying out Genie, not yet in production,
   governance requirements are not yet defined
5. **No existing dbt project** - adding dbt just for metrics is not worth it if
   there is no existing dbt transformation layer

---

## Part 5: Where dbt Semantic Layer Wins Decisively

The dbt Semantic Layer adds decisive value when:

1. **Auditability is required** - regulated industries, SOX compliance, any
   environment where "who approved this definition?" must have a traceable answer
2. **Multiple BI tools** - same metric must return the same number in Tableau,
   Genie, PowerBI, and your AI agents
3. **Complex metrics** - ratios, derived metrics, filtered measures, cumulative
   metrics, or metrics that span multiple models
4. **Multiple teams** - more than one team defines or consumes metrics;
   contracts and Mesh prevent breaking changes across team boundaries
5. **AI infrastructure** - AI agents (Claude, GPT, Copilot) need to query
   governed metrics via the dbt MCP server
6. **Fast-moving definitions** - metric definitions change frequently;
   PR-reviewed changes prevent definition drift
7. **Genie at scale** - dozens of users asking diverse questions; consistent
   metric definitions prevent different users getting different answers
8. **"Where does this number come from?"** - anyone needs to trace a Genie
   answer from the metric back to the raw source table with full lineage

---

## Part 6: Demo - Same Metric, Both Ways

This demo uses the `return_rate` metric, defined identically in both systems
for an apples-to-apples comparison.

### Metric Views version (02a_metric_view_orders.yml)

```yaml
- name: return_rate
  expr: >
    COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
    / CAST(COUNT(DISTINCT order_id) AS DOUBLE) * 100
  display_name: Return Rate (%)
  comment: Percentage of orders that were returned.
```

What Genie sees: a measure with a `comment` and a `display_name`.
What Genie doesn't see: that this metric is a ratio with an explicit
numerator and denominator, that the underlying data is tested, or that
the definition was PR-reviewed.

### dbt Semantic Layer version (cross-model metric in `_semantic_models.yml`)

```yaml
metrics:
  - name: return_rate
    label: "Order Return Rate (%)"
    description: >
      Percentage of orders that were returned. Computed as:
      returned_orders / total_orders * 100.
      Auditable because both inputs are governed simple metrics on fct_orders.
    type: ratio
    numerator:
      name: total_orders
      filter: "{{ Dimension('order__status') }} = 'returned'"
    denominator:
      name: total_orders
```

What Genie sees: a named metric with a label, a description, and an explicit
numerator/denominator - expressed semantically, not as raw SQL.

### Same Genie query on both

Ask Genie: *"What is our return rate?"*

| Aspect | Metric Views | dbt Semantic Layer |
|---|---|---|
| SQL generated | Evaluates the `expr` - raw SQL | Uses the ratio definition - semantic |
| Genie explanation | "return_rate from the metric view" | "Return rate = returned orders / total orders x 100" |
| Can Genie explain the denominator? | No - it's buried in the SQL expression | Yes - `order_count` is a separate, named measure |
| Auditability | UC audit log (timestamp + user ID) | `git log _marts.yml` (commit + PR + author + rationale) |
| Definition drift possible? | Yes - anyone with UC permissions can edit | No - PR required, review enforced by Git workflow |
| Downstream impact visibility | None - no contract, no consumers tracked | Catalog shows every model and metric that depends on this |

### The auditability check

Ask: *"When did the return rate definition change, and who approved it?"*

**Metric Views:** Check Unity Catalog audit logs. You'll find a timestamp and a
principal ID. You won't find the reason, the discussion, or the review approval.

**dbt Semantic Layer:**
```bash
$ git log --oneline platform/models/marts/_marts.yml
68b7194  Remove em dashes across all docs and repo text
e092d44  Refresh dbt + Databricks enablement for mid-2026
f7fa521  changing in the yml fixing dbt1505
323ccc0  fix: dbt0102 - use MetricFlow object syntax for all measure type_params
242699c  Adding Semantic Layer
```

Every change. Every reviewer. Every rationale. Immutable.

---

## Part 7: The Honest Assessment

Metric views are a genuine improvement over raw tables, and they are the natural
serving surface for Databricks-native tools like Genie and Databricks SQL. The
2026 point is that you no longer have to choose between them and dbt:

- **A metric view authored by hand in the catalog** = a named calculation with no
  version control, tests, or lineage
- **A metric view authored as a dbt model** (`materialized='metric_view'`) = the
  same Databricks-native object, now version-controlled, tested, and lineage-tracked
- **The dbt Semantic Layer** = a governed metric contract served to *every* tool
  (Tableau, Power BI, Looker, Python, AI agents) via one API - for stacks that
  reach beyond Databricks

dbt is the authoring and governance layer underneath both serving surfaces. The
choice is about where metrics are consumed, not whether dbt adds value.

**The question to ask your customer:**

> "When a CFO gets a revenue number from Genie and asks 'can I trust this?',
> what do you show them? A SQL expression in a catalog view - or a PR that was
> reviewed by the finance lead, tested by 7 automated checks, and traceable
> from the metric all the way back to the raw source table?"

If the answer matters to them - and in any enterprise it does - the dbt
Semantic Layer is not optional. It's the governance foundation that makes
Genie trustworthy.

---

## Part 8: The Genie Auditability Playbook

This is a step-by-step guide for demonstrating the full "trace a Genie answer"
workflow during the demo. Use this in Act 4 when the audience includes governance,
compliance, or leadership stakeholders.

### The 60-Second Audit (Live Demo)

The step-by-step runbook lives in **`DEMO_SCRIPT.md`, Part 4c-2** - that is the
single source of truth for how to run it, including the exact commands and the
real figures. It is not repeated here, because when it was, the two copies drifted
apart on step order and step count.

The short version: six questions, sixty seconds, from Genie's answer to a full
audit trail. What matters for *this* document is the contrast:

> "Try doing that with a hand-authored metric view. Step 1 works - you can read
> the SQL expression. The rest have no equivalent: no PR history of the
> definition's content, no data health tile, no contract to fail CI. You can see
> the metric, but you cannot audit how it got that way."

### What "Auditability" Really Means

The question-by-question comparison lives in **section 3.2 above** and is not
repeated here. It used to be, as a shorter five-row version, and the two copies
drifted: the short one still claimed metric views had no version history at all,
which is wrong and gets corrected on the call.

One table, one place. If you are adding a row, add it there.

### When to Use This in the Demo

- **Act 4c (Governance):** After showing the contract, run the 60-second audit
- **Q&A:** When someone asks "how do we audit Genie answers?" - this is the answer
- **Regulated industries:** Lead with this before showing anything else
- **CFO/VP audience:** "Let me show you how you'd answer your board when they
  ask where a number came from. It takes 60 seconds."

---

<!-- BEGIN GENERATED SOURCES - edit sources.yml, then run scripts/build_citations.py -->

## Sources

Generated from `sources.yml`. Every claim about a competitor's capabilities cites one of these. Do not edit by hand.

[^dbt-databricks-metric-view]: https://github.com/databricks/dbt-databricks/blob/main/CHANGELOG.md (retrieved 2026-08-10)
[^metric-views-joins]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/basic-modeling (retrieved 2026-08-10)
[^metric-views-yaml]: https://docs.databricks.com/aws/en/uc-semantics/metric-views (retrieved 2026-08-10)
[^uc-column-level-lineage]: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage (retrieved 2026-08-10)
[^uc-lineage-retention]: https://docs.databricks.com/aws/en/admin/system-tables/lineage (retrieved 2026-08-10)

<!-- END GENERATED SOURCES -->
