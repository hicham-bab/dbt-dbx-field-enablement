# Databricks Metric Views vs dbt Semantic Layer (MetricFlow)

An honest, side-by-side comparison for dbt field teams. This document answers
the question: "Our customer already has Databricks Metric Views — do they need
the dbt Semantic Layer?"

**Short answer:** Metric Views define *what to compute*. The dbt Semantic Layer
defines *what it means, who approved it, what tests guard it, and where the
data came from*. The first is a SQL view. The second is a governed, auditable,
multi-tool metric contract.

---

## Part 1: What Are These Two Things?

### Databricks Metric Views

Databricks Metric Views (introduced 2024, GA 2025) are YAML-defined metric
objects saved to Unity Catalog. They define measures, dimensions, and display
formatting. They appear as first-class objects in Genie and the SQL editor.

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
dimensions, measures) and named metrics in YAML files that live next to dbt
models in Git. Metrics are served via the Semantic Layer API (MetricFlow JDBC),
queryable by Genie, Tableau, PowerBI, Python SDK, and MCP-connected AI agents.

Example (from `platform/models/semantic/_semantic_models.yml`):

```yaml
- name: total_recognised_revenue
  label: "Total Recognised Revenue (USD)"
  description: >
    Revenue from completed orders only. This is the canonical definition
    of recognised revenue for this business. Genie uses this when a user
    asks about "revenue" without further qualification.
  type: simple
  type_params:
    measure:
      name: total_revenue
      filter: "{{ Dimension('order__status') }} = 'completed'"
```

**What you get:** A named, tested, version-controlled, PR-reviewed metric
definition that is served to every BI tool and AI agent via a single API.

---

## Part 2: The Feature Comparison

| Feature | Databricks Metric Views | dbt Semantic Layer (MetricFlow) |
|---|---|---|
| **Definition format** | YAML saved to Unity Catalog | YAML in Git, next to dbt models |
| **Version control** | No — saved to catalog, no git history | Yes — every change is a commit, every commit is reviewable |
| **PR review process** | None built-in | Yes — YAML + SQL in same PR, reviewed by data team |
| **Audit trail** | UC audit log (who modified the object) | `git log` (who changed what, when, why, PR link) |
| **Human-readable description** | `comment` field (optional) | `description` + `label` fields (fed to Genie) |
| **Metric types** | Measures only (aggregation expressions) | Simple, derived, ratio, cumulative, conversion |
| **Derived metrics** | Manual SQL expression | `derived` type — explicit formula referencing other metrics |
| **Ratio metrics** | Manual SQL division | `ratio` type — numerator/denominator declared separately |
| **Time grain handling** | Manual DATE_TRUNC in expr | MetricFlow handles `time_granularity` natively |
| **Dimension slicing** | Dimensions in same YAML | Entities + dimensions across semantic models (joins handled) |
| **Cross-model joins** | Not supported | Entity relationships — MetricFlow resolves joins automatically |
| **Data quality tests** | None on metric definitions | dbt tests on underlying marts (`not_null`, `accepted_values`, custom) |
| **Column contracts** | None | `contract: enforced: true` — schema changes fail CI |
| **Multi-tool compatibility** | Databricks tools only (Genie, SQL editor) | Any BI tool via Semantic Layer JDBC (Tableau, PowerBI, Looker, Genie) |
| **AI agent access** | Genie only | dbt MCP server — any AI agent can query metrics by name |
| **Cross-project (Mesh)** | Not supported | Yes — metrics from platform consumed by all downstream projects |
| **Governance (access control)** | UC permissions on the metric view | `access:` + `groups:` + UC permissions + contracts |
| **Breaking change detection** | None — metric silently breaks if source changes | `dbt build` fails if contract violated; downstream consumers fail in CI |
| **Lineage** | UC table-level lineage | dbt Explorer — column-level lineage from source to metric |
| **"Where does this number come from?"** | Read the SQL expression | Explorer → click metric → see full DAG from raw to metric |

---

## Part 3: The Big Narrative — Why This Distinction Matters

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
lack the governance layer — version control, PR review, tests, contracts, and
traceable lineage from metric to raw source.

The dbt Semantic Layer solves the trust problem end-to-end:

```
Raw source → dbt staging (tested) → dbt mart (contracted) → Semantic model → Named metric
     ↑              ↑                      ↑                      ↑              ↑
  source freshness  schema tests      column contracts     entity joins    PR-reviewed definition
                                      access: public       grain declared  git log audit trail
```

Every layer is tested, documented, and version-controlled. When a business user
asks "can I trust this number?", the answer is not "I think so" — it's
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
- No way to see what changed — only that something changed
- No way to see why — the business context behind the change is lost
- The `comment` field can be updated without any review process

**dbt Semantic Layer answer:**
```bash
$ git log --oneline platform/models/semantic/_semantic_models.yml

a3f7c21  Update revenue definition to exclude returned orders (#47)
9e2b134  Add return_rate ratio metric (#42)
6d1a8f0  Initial semantic models — 3 models, 8 metrics (#38)
```

- Every change has a commit hash, an author, a date, and a PR number
- The PR contains the discussion: why was the change made, who reviewed it,
  what tests were added
- The diff shows exactly what changed: "filter added: status = 'completed'"
- The full history is immutable and traceable

**Why this matters for Genie:**

When Genie returns a revenue number that doesn't match a dashboard, the
investigation path is completely different:

| Step | Metric Views | dbt Semantic Layer |
|---|---|---|
| 1. "What definition did Genie use?" | Read the metric view SQL expression | Click metric in Explorer → see definition + description |
| 2. "Is this the right definition?" | Ask the person who created the view | Check the PR that approved it — reviewer names are on record |
| 3. "When did it last change?" | UC audit log — timestamp only | `git log` — timestamp + author + PR + commit message |
| 4. "What changed?" | Compare current view to... nothing (no history) | `git diff` between any two commits |
| 5. "Where does the data come from?" | Read the `source:` field — one table reference | Explorer column-level lineage → full DAG from raw to metric |
| 6. "Is the underlying data correct?" | Run a manual query | dbt tests already validated it — check test results in Explorer |
| 7. "Can I prevent this from happening again?" | Add a comment and hope | Add a dbt test, enforce a contract, require PR review |

### 3.3 The "Where Does Genie's Answer Come From?" Workflow

This is the demo moment that resonates most with governance-conscious customers.
It answers the question every data leader eventually asks: **"I got a number from
Genie — show me exactly where it came from."**

**Step 1: Genie returns a number**

User asks: "What was total recognised revenue last month?"
Genie returns: $127,450.00

**Step 2: Trace the metric definition**

Open dbt Cloud Explorer → search "total_recognised_revenue" → click:

```
Metric: total_recognised_revenue
Label: "Total Recognised Revenue (USD)"
Description: Revenue from completed orders only. This is the canonical
             definition of recognised revenue for this business.
Type: simple
Measure: total_revenue
Filter: status = 'completed'
```

**Say:** "This is the definition Genie used. It's not a guess — it's a named
metric with an explicit filter. Revenue = completed orders only."

**Step 3: Trace the measure to the mart**

Click "total_revenue" measure → navigate to the semantic model → click the
underlying model: `fct_orders`

```
Model: fct_orders
Access: public
Contract: enforced
Column: amount_paid — "Total amount successfully paid for this order (USD).
         Counts only payments with status = 'success'."
```

**Say:** "The measure sums `amount_paid` from `fct_orders`. The column has a
contract — it must be `decimal(18,2)` and not null. If anyone changes the type,
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
Every hop is a dbt model — tested, documented, version-controlled. You can see
the full path from Genie's answer to the source table."

**Step 5: Verify data quality**

In Explorer, check the data health tile for `fct_orders`:

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
test ensures `status` can only be one of four values — the same values the
metric filter uses. If bad data enters, the tests catch it before Genie sees it."

**Step 6: Audit the definition history**

```bash
$ git log --oneline platform/models/semantic/_semantic_models.yml
a3f7c21  Update revenue definition to exclude returned orders (#47)
```

**Say:** "PR #47. Reviewed by the finance lead. The commit message says why:
'exclude returned orders.' The diff shows exactly what changed. When the auditor
asks 'who approved this?', you have a name, a date, and a discussion thread."

**The contrast — try this with Metric Views:**

> "Now try the same workflow with a Metric View. Step 1: Genie returns a number.
> Step 2: Find the metric view in the catalog, read the SQL expression. Step 3:
> The `source` field says `fct_orders`. How was `fct_orders` built? Read the
> notebook. Step 4: What tests validate the data? There are none on the metric
> view — you'd need to check the notebook's DLT expectations, if they exist.
> Step 5: Who approved this definition? Check the UC audit log — it shows a
> timestamp and a user ID, but not the rationale, the discussion, or the review."

### 3.4 The "Define Once, Serve Everywhere" Principle

This is the architectural argument that resonates with engineering leaders.

**Metric Views serve one ecosystem:** Databricks Genie and Databricks SQL.
If you also use Tableau, PowerBI, Looker, or a Python notebook — each tool
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
| Finance asks Genie: "total revenue?" | Returns $127,450 (from metric view) | Returns $127,450 (from Semantic Layer) |
| Analyst queries Tableau: "total revenue?" | Returns $131,200 (from Tableau's own calculation) | Returns $127,450 (same definition via JDBC) |
| DS team queries Python: "total revenue?" | Returns $129,800 (from notebook SQL) | Returns $127,450 (same definition via `dbt-sl-sdk`) |
| **CFO sees three different numbers** | "Which one is right?" | Doesn't happen — all three are the same |

This is the **single source of truth** problem. Metric Views solve it for
Databricks tools. The dbt Semantic Layer solves it for the entire stack.

### 3.5 The Governance Stack: What Each Layer Provides

The dbt Semantic Layer is not just a metric definition tool. It sits on top of
a governance stack that Metric Views don't have:

```
Layer 6: Named Metrics         → "total_recognised_revenue" queryable by name
Layer 5: Semantic Models       → Entities, dimensions, measures — grain declared
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

## Part 4: Where Metric Views Are Sufficient

Be honest. Metric Views are the right choice when:

1. **Simple, stable metrics** — fewer than 10 metrics, rarely change, no complex
   filters or time-grain requirements
2. **Databricks-only environment** — all BI consumers use Databricks SQL or Genie,
   no Tableau/PowerBI/Looker integration needed
3. **Small team, low governance overhead** — one person owns the metrics, manual
   sync is manageable
4. **Exploratory / prototype stage** — trying out Genie, not yet in production,
   governance requirements are not yet defined
5. **No existing dbt project** — adding dbt just for metrics is not worth it if
   there is no existing dbt transformation layer

---

## Part 5: Where dbt Semantic Layer Wins Decisively

The dbt Semantic Layer adds decisive value when:

1. **Auditability is required** — regulated industries, SOX compliance, any
   environment where "who approved this definition?" must have a traceable answer
2. **Multiple BI tools** — same metric must return the same number in Tableau,
   Genie, PowerBI, and your AI agents
3. **Complex metrics** — ratios, derived metrics, filtered measures, cumulative
   metrics, or metrics that span multiple models
4. **Multiple teams** — more than one team defines or consumes metrics;
   contracts and Mesh prevent breaking changes across team boundaries
5. **AI infrastructure** — AI agents (Claude, GPT, Copilot) need to query
   governed metrics via the dbt MCP server
6. **Fast-moving definitions** — metric definitions change frequently;
   PR-reviewed changes prevent definition drift
7. **Genie at scale** — dozens of users asking diverse questions; consistent
   metric definitions prevent different users getting different answers
8. **"Where does this number come from?"** — anyone needs to trace a Genie
   answer from the metric back to the raw source table with full lineage

---

## Part 6: Demo — Same Metric, Both Ways

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

### dbt Semantic Layer version (_semantic_models.yml)

```yaml
- name: return_rate
  label: "Order Return Rate (%)"
  description: >
    Percentage of orders that were returned. Computed as:
    returned_orders / total_orders * 100.
    This is a derived metric — auditable because both inputs are defined above.
  type: ratio
  type_params:
    numerator:
      name: order_count
      filter: "{{ Dimension('order__status') }} = 'returned'"
    denominator:
      name: order_count
```

What Genie sees: a named metric with a label, a description, and an explicit
numerator/denominator — expressed semantically, not as raw SQL.

### Same Genie query on both

Ask Genie: *"What is our return rate?"*

| Aspect | Metric Views | dbt Semantic Layer |
|---|---|---|
| SQL generated | Evaluates the `expr` — raw SQL | Uses the ratio definition — semantic |
| Genie explanation | "return_rate from the metric view" | "Return rate = returned orders / total orders x 100" |
| Can Genie explain the denominator? | No — it's buried in the SQL expression | Yes — `order_count` is a separate, named measure |
| Auditability | UC audit log (timestamp + user ID) | `git log _semantic_models.yml` (commit + PR + author + rationale) |
| Definition drift possible? | Yes — anyone with UC permissions can edit | No — PR required, review enforced by Git workflow |
| Downstream impact visibility | None — no contract, no consumers tracked | Explorer shows every model and metric that depends on this |

### The auditability check

Ask: *"When did the return rate definition change, and who approved it?"*

**Metric Views:** Check Unity Catalog audit logs. You'll find a timestamp and a
principal ID. You won't find the reason, the discussion, or the review approval.

**dbt Semantic Layer:**
```bash
$ git log --oneline platform/models/semantic/_semantic_models.yml
a3f7c21  Update revenue to exclude returned orders (#47)  — reviewed by @finance-lead
9e2b134  Add return_rate ratio metric (#42)                — reviewed by @analytics-eng
6d1a8f0  Initial semantic models (#38)                     — reviewed by @platform-team
```

Every change. Every reviewer. Every rationale. Immutable.

---

## Part 7: The Honest Assessment

Metric Views are a genuine improvement over raw tables. They give Genie named
metrics with display formatting and comments. For simple, Databricks-only use
cases with low governance requirements, they are sufficient.

The dbt Semantic Layer costs more to set up (YAML files, dbt Cloud license,
Semantic Layer configuration). But it provides a fundamentally different thing:

- **Metric Views = named calculation** saved to a catalog
- **dbt Semantic Layer = governed metric contract** backed by version control,
  tests, column contracts, cross-project Mesh, multi-tool API, and full lineage

**The question to ask your customer:**

> "When a CFO gets a revenue number from Genie and asks 'can I trust this?',
> what do you show them? A SQL expression in a catalog view — or a PR that was
> reviewed by the finance lead, tested by 7 automated checks, and traceable
> from the metric all the way back to the raw source table?"

If the answer matters to them — and in any enterprise it does — the dbt
Semantic Layer is not optional. It's the governance foundation that makes
Genie trustworthy.

---

## Part 8: The Genie Auditability Playbook

This is a step-by-step guide for demonstrating the full "trace a Genie answer"
workflow during the demo. Use this in Act 4 when the audience includes governance,
compliance, or leadership stakeholders.

### The 60-Second Audit (Live Demo)

**Setup:** Genie has just answered "What was total revenue last month?" with $127,450.

| Step | Action | What you show | Time |
|---|---|---|---|
| 1 | "What definition did Genie use?" | Open Explorer → search `total_recognised_revenue` → show definition, label, description, filter | 10s |
| 2 | "Who approved this definition?" | Terminal: `git log --oneline _semantic_models.yml` → show PR #47, author, date | 10s |
| 3 | "What changed in the last update?" | Terminal: `git diff HEAD~1 _semantic_models.yml` → show the filter that was added | 10s |
| 4 | "Where does the data come from?" | Explorer → `fct_orders` → column-level lineage → trace `amount_paid` back to `raw_payments` | 15s |
| 5 | "Is the data correct?" | Explorer → `fct_orders` data health tile → 7 tests passing, last run timestamp | 10s |
| 6 | "Can someone break this silently?" | Show `_marts.yml` → `contract: enforced: true` → "If anyone changes the schema, CI fails before production" | 5s |

**Total: 60 seconds.** From Genie's answer to full audit trail. No investigation,
no ticket, no "let me check with the team." The governance is in the code.

**The contrast line:**
> "Try doing this with a Metric View. Step 1 works — you can read the SQL
> expression. Steps 2–6 don't exist. There's no PR history, no column lineage,
> no data health tile, no contract. You can see the metric — but you can't
> audit it."

### What "Auditability" Really Means: The Five Questions

Every audit — whether from a CFO, a regulator, or an internal data quality
review — asks the same five questions. Here's how each system answers:

| Audit Question | Metric Views | dbt Semantic Layer |
|---|---|---|
| **What is the definition?** | Read the `expr` SQL in the metric view YAML | Read the metric definition in Explorer (description, type, filter, measure) |
| **Who approved it?** | UC audit log → principal ID + timestamp | `git log` → author + PR link + reviewer names + merge date |
| **What was the previous definition?** | Not available (no version history of the content) | `git diff` between any two commits — exact before/after |
| **What data feeds it?** | `source:` field → one table name | Explorer column-level lineage → full DAG from metric to raw table |
| **Is the data correct right now?** | Run a manual query and check | dbt tests → 7+ automated checks, data health tile in Explorer |

### When to Use This in the Demo

- **Act 4c (Governance):** After showing the contract, run the 60-second audit
- **Q&A:** When someone asks "how do we audit Genie answers?" — this is the answer
- **Regulated industries:** Lead with this before showing anything else
- **CFO/VP audience:** "Let me show you how you'd answer your board when they
  ask where a number came from. It takes 60 seconds."
