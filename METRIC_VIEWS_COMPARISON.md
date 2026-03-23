# Databricks Metric Views vs dbt Semantic Layer (MetricFlow)

An honest, side-by-side comparison for dbt field teams. This document answers
the question: "Our customer already has Databricks Metric Views — do they need
the dbt Semantic Layer?"

---

## What Are Databricks Metric Views?

Databricks Metric Views (introduced 2024) are SQL views in Unity Catalog that
define named metrics. You create them with standard `CREATE VIEW` DDL and they
appear as first-class objects in the Unity Catalog namespace.

Example (from `02_metric_views.sql`):

```sql
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.total_revenue AS
SELECT SUM(amount_paid) AS total_revenue
FROM enablement.ecommerce.fct_orders
WHERE status = 'completed';
```

They show up in Genie and can be queried like any other view.

---

## What Is the dbt Semantic Layer (MetricFlow)?

The dbt Semantic Layer uses MetricFlow to define semantic models (entities, dimensions,
measures) and named metrics in YAML files that live next to your dbt models.

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

---

## Side-by-Side Feature Comparison

| Feature | Databricks Metric Views | dbt Semantic Layer (MetricFlow) |
|---|---|---|
| **Definition location** | SQL DDL in UC | YAML next to dbt models |
| **Version control** | Manual (not automatic) | Git — every change is a commit |
| **PR review process** | None built-in | Yes — YAML + SQL in same PR |
| **Human-readable description** | No (SQL only) | Yes — `label` + `description` fields |
| **Genie context** | Column name only | Description + label fed to Genie |
| **Derived metrics** | Manual SQL calculation | `derived` metric type — explicit expression |
| **Ratio metrics** | Manual SQL division | `ratio` metric type — numerator/denominator declared |
| **Time grain handling** | Manual DATE_TRUNC | MetricFlow handles `time_granularity` |
| **Dimension slicing** | JOIN in SQL | Dimension entities — semantic, not SQL |
| **Data quality tests** | None on metric views | dbt tests on underlying marts |
| **Audit trail** | View DDL history | `git log _semantic_models.yml` |
| **Multi-tool compatibility** | Databricks tools only | Any BI via Semantic Layer API |
| **Cross-project (Mesh)** | Not supported | Yes — metrics from platform project used in consumers |
| **Governance (access control)** | UC permissions | `access:` + `groups:` + UC permissions |
| **Breaking change detection** | None | `dbt build` fails if contract violated |

---

## Where Metric Views Are Sufficient

Metric Views are the right choice when:

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

## Where dbt Semantic Layer Wins

The dbt Semantic Layer adds decisive value when:

1. **Complex metrics** — ratios, derived metrics, filtered measures, or metrics
   that require multiple hops through the data model
2. **Multi-tool environment** — same metric must return the same number in Tableau,
   Looker, Genie, and the internal API (the Semantic Layer API handles this)
3. **Regulated industries** — audit trails are required; "who approved this
   revenue definition?" must have a traceable answer
4. **Fast-moving definitions** — metric definitions change frequently;
   reviewing changes in PRs prevents definition drift
5. **Enterprise governance** — multiple teams own different parts of the data;
   contracts and access control prevent breaking changes
6. **dbt Mesh** — metrics need to be consistent across projects;
   the platform project's semantic layer is consumed by finance, marketing, etc.
7. **Genie at scale** — more than a handful of Genie users asking diverse questions;
   consistent metric definitions prevent different users getting different answers

---

## Demo: Same Metric, Both Ways

This demo uses the `return_rate` metric, which is defined identically in both systems
so the comparison is apples-to-apples.

### Step 1: Metric Views version

```sql
-- From 02_metric_views.sql
CREATE OR REPLACE VIEW enablement.ecommerce_metric_views.return_rate AS
SELECT
    COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END) AS returned_orders,
    COUNT(DISTINCT order_id)                                         AS total_orders,
    COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
        / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100     AS return_rate_pct
FROM enablement.ecommerce.fct_orders;
```

What Genie sees: a view named `return_rate` with three columns and no description.

### Step 2: dbt Semantic Layer version

```yaml
# From _semantic_models.yml
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
numerator/denominator breakdown — in the language of MetricFlow, not SQL.

### Step 3: Same Genie query on both

Ask in Genie: *"What is our return rate?"*

| Response aspect | Metric Views | dbt Semantic Layer |
|---|---|---|
| SQL generated | Queries the view — no context | Uses the ratio definition explicitly |
| Genie explanation | "return_rate_pct from the metric view" | "Return rate = returned orders / total orders × 100" |
| Auditability | View DDL only | `git log _semantic_models.yml` |
| Can Genie explain the denominator? | No | Yes — `order_count` with no filter |
| Definition drift possible? | Yes — view can change silently | PR required — change is visible and reviewed |

### Step 4: Auditability check

Ask: *"When did the return rate definition change?"*

**Metric Views answer:** Check the Unity Catalog audit logs for the view DDL.
This shows when the view was last modified, but not who reviewed the change.

**dbt Semantic Layer answer:**
```bash
git log platform/models/semantic/_semantic_models.yml
```
Shows every change, with author, date, and PR reference.

---

## The Honest Assessment

Metric Views are a genuine improvement over raw tables or unnamed columns.
For simple use cases, they are sufficient.

The dbt Semantic Layer costs more to set up but provides:
- A governance layer (PR review, audit trail) that Metric Views don't have
- A description layer that Genie can use to explain its answers
- A testing layer that validates the underlying data
- Multi-tool compatibility for enterprises with mixed BI environments

**The question to ask your customer:**
> "When a business user gets a revenue number from Genie and asks 'can I trust this?',
> what can they point to? A SQL view definition or a version-controlled YAML file
> with a PR history?"

If the answer matters to them, the dbt Semantic Layer matters.
