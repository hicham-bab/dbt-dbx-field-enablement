# 5-Act Demo Script: dbt + Databricks Field Enablement

**Total time:** 20–25 minutes
**Audience:** AEs, SAs, technical champions, or Databricks customers
**Setup required:** See pre-session checklist below

---

## Timing Table

| Act | Title | Time | What you show |
|-----|-------|------|---------------|
| 1 | The Problem: Genie on Raw Data | 3 min | Genie Space on raw tables — ambiguity |
| 2 | The Architecture | 5 min | How Raw → dbt Fusion → Semantic Layer → Genie works |
| 3 | Lakeflow Gold: Better But Not Enough | 5 min | Genie on Lakeflow gold — closer but still manual |
| 4 | dbt + Semantic Layer: The Solution | 10 min | Genie on dbt marts — accuracy, consistency, governance, auditability, Semantic Layer vs Metric Views |
| 4e | Fusion LSP + State-Aware Orchestration *(optional — technical audiences)* | +5 min | Live IDE intelligence + selective rebuilds vs Lakeflow |
| 4f | Data Science + Python Models *(optional — DS/ML audiences)* | +5 min | dbt Mesh for DS, Python models, single source of truth |
| 4g | dbt Platform vs Native dbt Task *(optional — "we'll self-host" objection)* | +5 min | Live comparison: native Databricks dbt task vs dbt Cloud |
| 5 | Business Close | 3 min | The "AND not OR" message + next steps |

---

## Pre-Session Checklist

Complete at least 30 minutes before the demo:

- [ ] `00_setup_raw_data.py` has run — all 5 raw tables exist in `enablement.ecommerce`
- [ ] `01_lakeflow_pipeline.py` has run — 13 Lakeflow tables in `enablement.ecommerce_lakeflow`
- [ ] `04_lakeflow_mesh_equivalent.py` has run — marketing + finance Lakeflow tables exist (contrast demo)
- [ ] `05a_lakeflow_data_science.py` has run — DS Lakeflow tables exist (Act 4f contrast)
- [ ] dbt Cloud `platform - full build` job is green — all 3 mart tables built, all tests pass
- [ ] dbt Cloud `marketing`, `finance`, and `data_science` jobs are green — consumer models built
- [ ] `02_metric_views.sql` has run — metric views exist in `enablement.ecommerce_metric_views`
- [ ] All 3 Genie Spaces are created and configured (raw, lakeflow, dbt)
- [ ] Databricks App is deployed and showing all 4 tabs
- [ ] Browser tabs open: Genie Spaces (all 3), dbt Cloud IDE with `_semantic_models.yml`, dbt Cloud lineage graph
- [ ] Fallback: `genie_demo_queries.md` open as backup if Genie is slow

---

## Act 1: The Problem (3 min)

**Goal:** Establish why raw data + Genie = unreliable answers.

**Open:** Genie Space `E-Commerce (Raw — Act 1)`

**Run these queries and let the audience see the ambiguity:**

1. *"What was total revenue last month?"*
   - Genie picks `amount` from `raw_orders` or `raw_payments` — both exist, both plausible
   - **Say:** "Notice Genie had to guess which column means revenue. The `amount` column
     exists in both `raw_orders` and `raw_payments`. Which one is revenue? Genie guesses."

2. *"How many high-value customers do we have?"*
   - Genie doesn't know what "high-value" means — no definition in raw tables
   - **Say:** "Business concepts like 'high-value' don't exist in raw data.
     Genie has to make one up — or fail."

3. *"What is our return rate?"*
   - Genie computes something — denominator is ambiguous
   - **Say:** "Even a simple metric requires knowing the denominator.
     All orders? Only completed? Genie guesses. Every time."

**Closing line for Act 1:**
> "This is not a Genie failure. This is a metadata failure. Genie is only as good
> as the context you give it. The answer isn't a better prompt — it's better data."

---

## Act 2: The Architecture (5 min)

**Goal:** Explain the solution architecture before showing it live.

**Show:** Architecture diagram (or draw it live)

```
Raw Delta Tables  →  dbt Fusion  →  Tested Marts  →  Semantic Layer  →  Genie
(enablement.ecommerce)              (contracts)      (_semantic_models.yml)
        ↓
Lakeflow Pipeline  →  Gold Tables  →  Genie
(manual instructions)
```

**Key points to make:**

1. **dbt is not replacing Lakeflow.** Lakeflow handles ingestion and streaming.
   dbt handles the business transformation layer — where business logic needs to
   be testable, documented, and reviewable.

2. **Three layers of context for Genie:**
   - Unity Catalog column metadata pushed by `dbt-databricks` adapter (`persist_docs`)
   - Genie Space instructions generated from `schema.yml`
   - Semantic Layer metrics from `_semantic_models.yml`

3. **Why this matters:**
   - Column descriptions flow from YAML → Unity Catalog → Genie automatically
   - Business rule definitions (revenue = completed orders) are in YAML, not notebooks
   - The semantic layer gives Genie named metrics with explicit filters

4. **Lakeflow vs dbt — complementary:**
   - Lakeflow is excellent for Python-heavy, streaming, and ingestion pipelines
   - dbt is excellent for SQL-based business logic, documentation, and governance
   - Most enterprise customers use both: Lakeflow for Bronze/Silver, dbt for Gold/Marts

**Transition:**
> "Let me show you what happens when you give Genie slightly better data — the
> Lakeflow gold layer — and then what happens when you give it the full dbt context."

---

## Act 3: Spark Declarative Pipelines Gold — Better But Not Enough (5 min)

**Goal:** Show that Spark Declarative Pipelines (SDP, formerly DLT/Lakeflow) alone improve Genie but don't solve the governance problem.

**Open:** Genie Space `E-Commerce (Lakeflow Gold — Act 3)`

**Run the same questions as Act 1:**

1. *"What was total revenue last month?"*
   - Better — Genie finds `daily_revenue` in `gold_fct_revenue`
   - **Say:** "Better. Lakeflow gold has cleaner structure. But the definition
     of `daily_revenue` lives in a Python SDP notebook. The instruction I wrote
     manually says 'completed orders only' — but I had to write that. If the
     pipeline changes, I have to remember to update these instructions too."

2. *"Show me revenue by customer segment"*
   - Works — but only because you wrote the instructions manually
   - **Say:** "This works now. But notice why: I wrote the segment definition
     manually in the Genie Space instructions. This isn't connected to the code.
     If a developer changes the segmentation logic in the SDP notebook,
     these instructions don't update automatically."

3. *"What is our return rate?"*
   - Closer — but ratio definition still manual
   - **Say:** "Still no formal definition of this ratio. Still guessing."

**The key moment — show the Genie Space instructions:**

> "Here is the Genie instruction I wrote manually for Lakeflow. Notice it took me
> 10 minutes to write. It has no connection to the SDP code. If the code changes,
> I have to update this by hand. This is the problem dbt solves — let me show you Act 4."

---

## Act 4: dbt + Semantic Layer — The Solution (8 min)

**Goal:** Show accuracy, consistency, complexity, and governance.

**Open:** Genie Space `E-Commerce Analytics (dbt + Semantic Layer — Act 4)`

### Part 4a: Accuracy (2 min)

1. *"What was total revenue last month?"*
   - Genie uses `SUM(amount_paid) WHERE status = 'completed'` — exact match
   - **Say:** "Same question, third time. Now Genie used the exact SQL that matches
     our business definition. How do I know? Because that definition is in this file."

   **Open `platform/models/semantic/_semantic_models.yml`:**
   ```yaml
   - name: total_recognised_revenue
     description: >
       Revenue from completed orders only. This is the canonical definition
       of recognised revenue for this business.
   ```
   **Say:** "The definition lives here. In a YAML file. In Git. Reviewable in a PR."

2. *"Show me revenue by customer segment"*
   - Perfect — join uses tested FK, segment uses accepted_values
   - **Say:** "This works because `customer_segment` has only three possible values,
     tested with `accepted_values` in our schema YAML. It cannot be wrong."

### Part 4b: Consistency (2 min)

3. *"What percentage of revenue comes from high-value customers?"*
   - Complex two-step calculation — Genie handles it correctly
   - **Say:** "A complex question that requires joining two concepts. Genie gets it
     right because both 'revenue' and 'high-value' are precisely defined in the same
     YAML that dbt uses for testing."

4. *"Which customers are at risk of churning?"*
   - Uses `most_recent_order_date`, applies the 90-day threshold from instructions
   - **Say:** "The definition of 'at risk' is in our Genie instructions — which came
     from our `schema.yml`. Not from Genie's training data. From our code."

### Part 4c: Governance — The Key Moment (3 min)

**Show the contract:**

> "Let me show you something that doesn't exist in Lakeflow."

Open `platform/models/marts/_marts.yml` and show `fct_orders`:
```yaml
- name: fct_orders
  access: public
  config:
    contract:
      enforced: true
  columns:
    - name: amount_paid
      data_type: decimal
      constraints:
        - type: not_null
```

**Say:** "This is a contract. When the `marketing` or `finance` team's dbt build runs,
it validates that `amount_paid` is still a decimal and still not null.
If someone upstream changes the schema, their build fails. Not a production incident —
a build failure in CI/CD."

**Show cross-project ref:**

Open `finance/models/fct_revenue.sql`:
```sql
select * from {{ ref('platform', 'fct_orders') }}
```

**Say:** "This is dbt Mesh. The finance team's model depends on the platform team's
`fct_orders`. The platform team cannot change `fct_orders` without the finance
team's build failing first. Governance enforced by the build system."

**The audit trail moment:**

In terminal:
```bash
git log platform/models/semantic/_semantic_models.yml
```

**Say:** "When a CFO asks 'who approved the revenue definition?', this is the answer.
Commit hash. Author. Date. PR number. Every change is traceable. This is what
enterprise governance looks like."

### Part 4c-2: The 60-Second Audit — "Where Did Genie's Answer Come From?" (2 min)

This is the highest-impact demo moment for governance audiences. Run it immediately
after the contract walkthrough.

**Setup line:**
> "A CFO just saw Genie return $127,450 as total revenue. They ask: 'Where did
> that number come from? Can I trust it?' Let me show you how we answer that —
> in 60 seconds."

**Step 1 — What definition did Genie use? (10s)**

Open dbt Cloud Explorer, search `total_recognised_revenue`:

```
Metric: total_recognised_revenue
Label: "Total Recognised Revenue (USD)"
Filter: status = 'completed'
```

**Say:** "Named metric. Explicit filter. Genie didn't guess — it used this definition."

**Step 2 — Who approved this definition? (10s)**

```bash
git log --oneline platform/models/semantic/_semantic_models.yml
```

**Say:** "PR #47. Reviewed by the finance lead. Merged on March 12th.
That's your audit trail."

**Step 3 — Where does the data come from? (15s)**

In Explorer, click `fct_orders` → column-level lineage → trace `amount_paid`:

```
total_recognised_revenue (metric)
  → fct_orders.amount_paid (contracted, tested)
    → stg_payments.amount (staging)
      → raw_payments.amount (raw source)
```

**Say:** "From the metric all the way to the raw table. Every hop is a dbt model —
tested, documented, version-controlled. Four clicks. No investigation ticket."

**Step 4 — Is the data correct? (10s)**

Show the data health tile for `fct_orders` in Explorer:

```
✓ 7 tests passing — last run: 2 hours ago
```

**Say:** "Seven automated tests validated this data on the last run. Including
a custom test that ensures no negative amounts."

**Step 5 — Can someone break this silently? (5s)**

Point back to `contract: enforced: true` from Part 4c.

**Say:** "No. If anyone changes the schema, CI fails. If anyone changes the
metric definition, it goes through a PR. If the data fails a test, the build
stops. There is no silent breakage path."

**The contrast line (the closer):**

> "Now try this with a Metric View. You can see the SQL expression — that's Step 1.
> Steps 2 through 5 don't exist. No PR history. No column lineage. No data health
> tile. No contract. You can see the metric. You cannot audit it."

> "See `METRIC_VIEWS_COMPARISON.md` for the full side-by-side."

---

### Part 4d: Semantic Layer vs Metric Views — Define Once, Serve Everywhere (2 min)

**Setup line:**
> "Let me show you the architectural difference between Metric Views and the
> dbt Semantic Layer — it's not just about where the YAML lives."

**Show the single-endpoint architecture:**

```
                                  ┌─── Genie (via JDBC)
                                  │
_semantic_models.yml ──► JDBC ────┼─── Tableau
  (one definition)     endpoint   ├─── PowerBI
                                  ├─── Python SDK
                                  └─── AI agents (MCP server)
```

**Say:** "One YAML file. One definition. One JDBC endpoint. Every tool — Genie,
Tableau, PowerBI, Python notebooks, AI agents — gets the same number. Not a copy.
The same computation, from the same definition, served by the same API."

**The Metric Views contrast:**

> "Metric Views serve Databricks tools only. If you also use Tableau or PowerBI —
> and most enterprises do — each tool defines its own version of 'revenue'.
> You get three numbers for the same question. The dbt Semantic Layer gives you one."

**Show the complexity advantage:**

Point to `return_rate` (ratio metric) and `revenue_per_customer` (derived metric)
in `_semantic_models.yml`:

**Say:** "Ratio metrics. Derived metrics. Cumulative metrics. Time-grain-aware
calculations. Metric Views support measures — aggregation expressions. The dbt
Semantic Layer supports metric *types* — semantic constructs that MetricFlow
resolves into correct SQL for any time grain, any filter, any dimension slice.
That's why Genie can answer 'what was the return rate by country last quarter?'
correctly — MetricFlow handles the grain, the filter, and the join."

**The one-liner:**
> "Metric Views are named calculations. The dbt Semantic Layer is a governed
> metric contract. The difference is what happens when someone asks 'can I trust
> this number?'"

---

## Act 4d-2: dbt MCP Server + AI Agent Skills *(optional — AI/agentic audiences, +8 min)*

**Goal:** Show how easy it is to install the dbt MCP Server with dbt Agent skills,
then demonstrate an AI agent querying governed metrics from the Semantic Layer,
auditing skills for security, and checking test results and deployment jobs —
all from a single conversational interface.

**When to use this act:** Customer is exploring AI agents, Copilot integrations,
or asks "how do AI tools consume governed metrics?" This is the natural follow-up
to Act 4d's "AI agents (MCP server)" row in the architecture diagram.

---

### Part 4d-2a: Installing the dbt MCP Server (2 min)

**The setup line:**
> "You've seen the Semantic Layer serves Genie, Tableau, PowerBI through one JDBC
> endpoint. Now let me show you how AI agents — Claude, Cursor, VS Code Copilot —
> consume those same governed metrics. It takes 60 seconds to set up."

**Show the installation:**

Open your AI tool's MCP configuration (e.g., Claude Desktop `claude_desktop_config.json`,
Claude Code `settings.json`, or Cursor MCP settings) and add:

```json
{
  "mcpServers": {
    "dbt": {
      "command": "npx",
      "args": ["-y", "@dbt-labs/dbt-mcp"],
      "env": {
        "DBT_HOST": "your-account.us1.dbt.com",
        "DBT_TOKEN": "<your-service-token>",
        "DBT_PROD_ENV_ID": "<your-production-environment-id>"
      }
    }
  }
}
```

**Say:** "Three environment variables. One `npx` command. No infrastructure.
The MCP server gives your AI agent access to the full dbt platform — semantic
metrics, model metadata, job runs, test results — through the same governed
definitions you just saw. The agent doesn't guess SQL. It calls MetricFlow."

**If the customer asks "what about security?":**
> "The service token has scoped permissions — same RBAC as any dbt Cloud API consumer.
> The agent can only see projects and environments that the token grants access to.
> And every query goes through the Semantic Layer, so it's the same governed metric
> definition — not raw SQL the agent invented."

---

### Part 4d-2b: Querying the Semantic Layer via MCP (3 min)

**The setup line:**
> "Let me ask the AI agent the same questions we asked Genie — but this time,
> the agent has full dbt context, not just table metadata."

**Live demo — ask the agent natural language questions:**

In your MCP-connected AI tool (Claude Code, Claude Desktop, or Cursor), type:

> "What was total recognised revenue last quarter, broken down by country?"

**Point out what happens under the hood:**

> "The agent didn't write SQL. It called the `query_metrics` tool from the dbt MCP
> server, which invoked MetricFlow with the `total_recognised_revenue` metric,
> the `country` dimension, and a time filter. Same metric definition. Same JDBC
> endpoint. Same number you'd get in Genie, Tableau, or PowerBI."

**Follow up with a complex question:**

> "What's the return rate by product category for customers in the high-value segment?"

**Say:** "This joins the `return_rate` ratio metric with `category` from the products
semantic model and `customer_segment` from the customers semantic model. MetricFlow
resolves the joins automatically — the agent doesn't need to know the schema. It
just names the metric and the dimensions."

**The contrast:**

> "Without the Semantic Layer, the AI agent would generate raw SQL — guessing
> joins, guessing filters, guessing what 'return rate' means. With the dbt MCP
> server, it asks MetricFlow. The answer is governed by the same definition
> your finance team approved in a PR."

---

### Part 4d-2c: Auditing Agent Skills (1 min)

**The setup line:**
> "When you give an AI agent access to your data platform, the first question
> from security is: 'what can it actually do?' Let me show you."

**Show the skill audit:**

Ask the agent to list its available dbt tools:

> "What dbt tools and skills do you have access to?"

**Point to the tool list:**

> "Every capability is an explicit MCP tool — `query_metrics`, `get_model_details`,
> `list_jobs`, `get_job_run_details`, `get_test_details`. There are no hidden
> actions. The agent can read metadata and query governed metrics. It cannot
> modify models, trigger deployments, or access raw tables outside the Semantic
> Layer. This is auditable by design — your security team can review exactly
> what the service token permits and what tools the MCP server exposes."

**If the audience is security-conscious:**

> "You can also run an audit on the MCP skills themselves — checking for
> prompt injection risks, overly broad permissions, or data exfiltration paths.
> The dbt MCP server publishes its tool schemas, so automated security scanners
> can verify what each tool does before you deploy it to production agents."

---

### Part 4d-2d: Checking Tests and Deployment Jobs (2 min)

**The setup line:**
> "The agent doesn't just answer data questions. It can also tell you whether
> your pipeline is healthy — same information your team checks in the dbt Cloud UI,
> but from a conversation."

**Live demo — check job status:**

> "Show me the latest deployment job runs and their status."

**Point out the response:**

> "The agent called `list_jobs` and `list_jobs_runs` from the dbt MCP server.
> You can see which jobs succeeded, which failed, when they ran, and how long
> they took. No need to switch to the dbt Cloud UI."

**Follow up — drill into test results:**

> "Were there any test failures in the last production run?"

**Say:** "The agent called `get_job_run_details` and then `get_job_run_error` to
inspect the run. It shows you exactly which tests passed, which failed, and the
error details. Your on-call engineer gets the same information they'd find in
the dbt Cloud run page — but in a chat interface they can query conversationally."

**Show the audit trail connection:**

> "This connects back to the 60-second audit from Act 4c-2. The agent can:
> 1. Answer a metric question → `query_metrics`
> 2. Show you the metric definition → `get_model_details`
> 3. Show you the test results → `get_test_details`
> 4. Show you the last job run → `get_job_run_details`
> 5. Show you the model lineage → `get_lineage`
>
> That's the full audit trail — from answer to definition to tests to deployment —
> in a single conversation. No tab-switching. No context loss."

**The closing line for Act 4d-2:**
> "The dbt MCP Server turns your AI agent from a SQL generator into a governed
> analytics assistant. It doesn't guess — it uses the same metric definitions,
> the same test suite, and the same deployment metadata that your team already
> trusts. And it took 60 seconds to install."

---

## Act 4e: Fusion LSP + State-Aware Orchestration *(optional — technical audiences, +5 min)*

**Goal:** Show two developer-experience advantages that have no equivalent in Databricks:
the Fusion compiler giving instant feedback in the IDE, and dbt only rebuilding what changed.

**When to use this act:** SA-to-SA conversations, data engineering teams, or when the
audience asks "what does Fusion actually give us beyond faster parsing?"

---

### Part 4e-1: Fusion LSP — Errors at Typing Time, Not Runtime (2 min)

**The setup line:**
> "In Databricks notebooks, you find out a table doesn't exist when the pipeline fails.
> With Fusion running in dbt Cloud Studio, you find out while you're typing."

**Live demo — introduce a typo:**

1. Open `finance/models/fct_revenue.sql` in dbt Cloud Studio
2. Change `{{ ref('platform', 'fct_orders') }}` to `{{ ref('platform', 'fct_orderss') }}`
3. **Point to the red underline that appears immediately — before saving, before running**
4. **Say:** "That's the Fusion compiler running in real time as a Language Server.
   It knows the full DAG of all three projects and validated that `fct_orderss`
   does not exist in the platform project. Zero latency. No job run needed."
5. Revert the typo

**Live demo — contract violation:**

1. Open `platform/models/marts/_marts.yml`
2. Change `data_type: bigint` on `number_of_orders` to `data_type: varchar`
3. **Immediate warning in the Problems panel**
4. **Say:** "The contract says this column must be a bigint. I changed it to varchar.
   Fusion flagged it before I could even save the file. In a Databricks SDP notebook,
   this would only fail when a downstream consumer runs and finds the wrong type.
   By then it may be in production."
5. Revert

**If someone says "Databricks notebooks check errors too" — use this:**

> "Databricks checks if the *table exists in Unity Catalog*.
> Fusion checks if the *reference is valid in your dbt project* —
> including whether the model is `access: public`, whether the contract columns
> still match, and whether the downstream DAG is still consistent.
> Those are different questions. Databricks answers 'does this object exist?'
> Fusion answers 'is this dependency correct, safe, and contract-compliant?'"

**The contrast table — say this out loud:**

| Scenario | dbt + Fusion LSP | Databricks Notebook |
|---|---|---|
| Typo in table name | Red underline instantly — DAG-aware | Red underline — UC object lookup only |
| Contract violation | Flagged before save | No contract concept — silent |
| Cross-project ref to a protected model | Compile error: model is not public | No access tier enforcement |
| Wrong column type vs contract | Immediate warning | Only fails at consumer runtime |
| Autocomplete for `ref()` | Full model list with access tiers | Table browser — no dbt DAG awareness |

---

### Part 4e-2: State-Aware Orchestration — Only Rebuild What Changed (3 min)

**The setup line:**
> "When your pipeline has 200 models and an analyst changes one staging model,
> how much do you rerun? In Lakeflow, everything. In dbt, only what actually changed."

**Show the concept with this project:**

Open the dbt Cloud Studio terminal and run:

```bash
dbt build --select state:modified+
```

**Say:** "This command compares the current code against the last production run's
`manifest.json`. It finds every model that changed, then traverses the DAG forward
to find every downstream dependent. It runs exactly those models — nothing else."

**Make it concrete — walk through a scenario:**

> "Say an analyst changes the segmentation threshold in `stg_customers.sql` —
> moving 'high_value' from $500 to $600. With `state:modified+`, dbt runs:
> `stg_customers → int_customer_orders → dim_customers → mart_customer_segments`.
> That's 4 models out of 10. The finance models don't run. The product dimension
> doesn't run. Only the affected path."

**Show what Lakeflow does instead:**

Open `databricks/notebooks/04a_lakeflow_marketing.sql` and point to line 77:

```sql
FROM enablement.ecommerce_lakeflow.gold_dim_customers c
```

**Say:** "There is no equivalent here. This pipeline has no awareness of what changed
in the platform pipeline. It reruns fully every time — or you manually maintain a list
of which tables to refresh. At 10 tables that's manageable. At 200 it becomes a
scheduling and cost problem."

**The closing line for Act 4e:**
> "State-aware orchestration is not a feature you notice when your project has 10 models.
> It's the feature that saves you 40 minutes of compute time per CI run when you have 300.
> And it's built into `dbt build` — no configuration required."

---

## Act 4f: Data Science + Python Models *(optional — DS/ML audiences, +5 min)*

**Goal:** Show that the DS team can use Python models in dbt, consume governed
platform marts via Mesh, and avoid the duplication trap that Lakeflow creates.

**When to use this act:** DS/ML teams in the audience, "our team is Python-native"
objection, or when the customer asks about feature engineering workflows.

---

### Part 4f-1: The Duplication Problem (2 min)

**The setup line:**
> "Your DS team needs customer features for churn prediction. In Databricks without
> dbt, they have two options: duplicate the transformation logic in a notebook,
> or read from the platform tables with no contract enforcement. Both are problems."

**Show the Lakeflow version:**

Open `databricks/notebooks/05a_lakeflow_data_science.py` and point to:

```python
customers = spark.read.table("enablement.ecommerce_lakeflow.gold_dim_customers")
```

**Say:** "Hardcoded table reference. No validation. If the platform team renames
`total_lifetime_value` to `ltv`, this pipeline fails at runtime — after it has
already started processing. Worse: the `$500` high-value threshold is duplicated
here. When the business changes that threshold, someone has to find every notebook
that uses it. With 3 teams, that's 3 notebooks. With 30 teams, it's 30."

### Part 4f-2: The dbt Mesh Solution (2 min)

**Show the dbt Python model:**

Open `data_science/models/features/rfm_customer_features.py`:

```python
customers = dbt.ref("platform", "dim_customers")
orders = dbt.ref("platform", "fct_orders")
```

**Say:** "Same PySpark code the DS team already knows. The only difference is the
first two lines: `dbt.ref()` instead of `spark.read.table()`. That one change gives you:
1. Compile-time validation — if the platform changes `dim_customers`, this build fails immediately
2. Contract enforcement — the DS team knows the column types won't change without a PR
3. Full lineage — dbt Cloud Explorer shows DS depends on platform, same graph as marketing and finance
4. Single source of truth — the `customer_segment` definition comes from platform, not duplicated"

### Part 4f-3: Python-Native Use Cases (1 min)

**Show `customer_churn_features.py`:**

**Say:** "Feature engineering for ML — window functions, inter-order gap calculation,
behavioral signals. This is PySpark, running on your Databricks cluster. dbt doesn't
force you to use SQL — it lets you use the right tool while participating in the
governed DAG. The `is_churned` label, the `return_rate` calculation — all defined once,
tested, documented, and consumed by any downstream model or notebook."

**The key question to ask:**
> "How many data scientists in your org are duplicating the same customer features
> in different notebooks right now? With dbt Mesh, they define it once and share it."

### Part 4f-4: The Cost Argument (1 min — use if "dbt is an extra cost" comes up)

**Say:** "Let me address cost directly. Notebooks are free. But the infrastructure
you build around them is not. There are three cost dimensions, and two of them
are mechanically provable."

**Dimension 1 — CI compute (provable):**

> "`state:modified+` rebuilds only what changed. In this demo, a typical PR
> modifies 1–3 models with ~10 downstream dependents. That's 13 models out of
> 200 — a 93% reduction per CI run. Multiply that by your PRs per month and
> your DBU cost per model-run. That's real money — and the ratio gets better
> as your project grows."

**Dimension 2 — Duplication (countable):**

> "Without Mesh, marketing, finance, and data science each re-run the customer
> and order aggregations independently. That's 3 shared models × 3 extra teams ×
> 30 daily runs = 270 redundant model-runs per month. With Mesh, those are
> `ref()` calls — zero re-computation."

**Dimension 3 — Engineering time (discoverable):**

> "Ask your team: how many hours per month do they spend on cross-project job
> wiring, documentation maintenance, metric discrepancy investigations, and
> CI/CD setup? Those are activities that dbt Cloud provides as a managed service.
> The compute savings are meaningful. The engineering savings are usually 10–20x
> larger."

**Say:** "The framework is in `BATTLE_CARD.md` Part 5. We can build the TCO with
your numbers in 15 minutes — pull up your SQL Warehouse query history and let's
count."

---

## Act 4g: dbt Platform vs Native Databricks dbt Task *(optional — "we'll self-host" objection, +5 min)*

**Goal:** Concretely demonstrate what the customer loses by using the native
Databricks dbt task instead of dbt Platform (Cloud).

**When to use this act:** Customer says "we'll just use the native dbt task in
Databricks Jobs" or "we don't need dbt Cloud, we can self-host dbt Core."

---

### Part 4g-1: What the Native Task Actually Is (1 min)

**Say:** "Let me be precise about what the native dbt task gives you. It's dbt Core —
the open-source Python compiler — running on Databricks compute, triggered by a
Databricks Job. It executes `dbt build`. That's it. Everything else — the IDE,
Explorer, Semantic Layer, CI/CD environments, Fusion compiler — is not included."

**Show this table (or say it out loud):**

| Capability | Native dbt Task | dbt Platform |
|---|---|---|
| Runs `dbt build` | Yes | Yes |
| Managed IDE with lineage | No | Yes |
| CI/CD environments (dev/staging/prod) | Manual | Yes |
| Explorer (searchable model catalog) | No | Yes |
| Column-level lineage | No | Yes |
| Semantic Layer JDBC | **No** | **Yes** |
| Genie queries governed metrics | **No** | **Yes** |
| Fusion compiler (10-40x faster) | No | Yes |
| dbt Copilot / AI features | No | Yes |

### Part 4g-2: The Week-6 Moment (2 min)

**Say:** "The native task looks fine for the first 4 weeks. `dbt build` runs,
tests pass, tables materialise. Then in week 5-6, you connect Genie to your
dbt mart tables and a business user asks 'what was total revenue last month?'"

**Walk through the scenario:**

> "Genie generates SQL. Without the Semantic Layer, it picks `SUM(amount_paid)`
> from `fct_orders` — including returned orders. Your finance team says the number
> is wrong. You realise you need the `total_recognised_revenue` metric that filters
> to `status = 'completed'`. But that metric lives in `_semantic_models.yml` and
> is served by the Semantic Layer JDBC endpoint. The native task doesn't have that.
> You're now 6 weeks into an MVP, and you need to migrate to dbt Cloud to get the
> one feature that makes Genie trustworthy."

### Part 4g-3: The Orchestration Gap (2 min)

**Say:** "Beyond the Semantic Layer, there's the orchestration question. The native
dbt task runs in a Databricks Job. That's fine for a single project. But you have
four dbt projects — platform, marketing, finance, data science. Each depends on
platform. In dbt Cloud, cross-project dependencies are handled automatically:
when platform finishes, downstream projects trigger. With the native task, you're
manually chaining Databricks Jobs with task dependencies, hoping the timing is right."

**Show the contrast:**

> "In dbt Cloud: define the dependency in `dependencies.yml`, deploy. Done.
> Cross-project state awareness, automatic triggering, shared artifacts.
>
> With native dbt tasks: create 4 Databricks Jobs, manually wire task dependencies,
> manage `manifest.json` passing between jobs for state comparison, build your own
> CI/CD per project. That's a sprint of infrastructure work — and you still don't
> get the Semantic Layer."

**The closing line:**
> "The native dbt task saves you the dbt Cloud license in week 1.
> It costs you 2-3 weeks of rebuild in week 6 when you need the Semantic Layer.
> The question is when you want to pay — not whether."

---

## Act 5: Business Close (3 min)

### For technical audiences (SAs, data engineers)

> "The question isn't 'dbt OR Databricks'. It's 'what does each do best?'
>
> Lakeflow is excellent for what it does — declarative Python pipelines, streaming,
> auto-lineage in Unity Catalog. We're not replacing that.
>
> dbt adds the governance layer that Lakeflow doesn't have: version-controlled
> business logic, column-level tests, semantic metrics, and the Mesh architecture
> for multi-team governance.
>
> The customer who has both gets the best of each: Lakeflow handles the data
> movement, dbt handles the business transformation layer that stakeholders trust."

### For business audiences (AEs, Champions, VP+)

> "The question Databricks asks is: 'if we have Lakeflow, why do we need dbt?'
>
> The answer is: Lakeflow moves the data. dbt makes it trustworthy.
>
> When a CFO looks at a Genie answer and asks 'can I trust this number?',
> dbt is the thing that lets you say yes — and prove it with a git history,
> a PR review, and a test suite."

### Next steps

- "Connect dbt Fusion to your Databricks workspace — 15-minute setup, see SETUP.md"
- "Run `dbt build` on the platform project — 10 models, all tests pass"
- "Create a Genie Space on the dbt marts — compare it to your current setup"

---

## Q&A Anchors

**"We already have Lakeflow — why add dbt?"**
> "Lakeflow solves data movement. dbt solves data governance. They solve different
> problems. Show me your current Genie Space — do your column descriptions come
> from code or from manual entry?"

**"This looks like more complexity."**
> "It's more structure, not more complexity. The alternative is manually maintaining
> Genie instructions, manually writing column descriptions, and hoping the SDP
> notebook stays in sync with the documentation. dbt automates all of that."

**"Our team is Python-native, not SQL."**
> "dbt supports Python models — and this demo has three of them. The `data_science`
> project runs PySpark feature engineering on Databricks while consuming governed
> platform marts via Mesh. Same `dbt.ref()`, same contracts, same lineage.
> Open `rfm_customer_features.py` — it's PySpark, not SQL. dbt doesn't force a
> language — it adds governance to whatever language your team already uses."

**"We'll just use the native dbt task in Databricks Jobs."**
> "The native task runs `dbt build`. That's it. No Semantic Layer, no Explorer,
> no managed CI/CD, no Fusion compiler. It works until week 6 when you connect
> Genie and realise you can't serve governed metrics. See Act 4g for the full story."

**"How do AI agents get governed answers instead of hallucinating SQL?"**
> "The dbt MCP Server. It gives AI agents access to the Semantic Layer via MetricFlow,
> not raw table access. The agent calls `query_metrics` with named metrics and dimensions —
> same definitions your team approved in a PR. No SQL guessing. See Act 4d-2."

**"How does this work with dbt Cloud?"**
> "This is dbt Cloud. The three projects — platform, marketing, finance — each have
> their own dbt Cloud project with their own deployment job and CI. The Fusion compiler
> runs inside dbt Cloud on every job run. What you see here is a production setup,
> not a local demo."

---

## If the Demo Breaks

| Problem | Recovery |
|---|---|
| Genie is slow / down | Switch to the Streamlit app — Tab 3 shows the comparison with data |
| dbt Cloud job hasn't run | Show the SQL files and YAML in the dbt Cloud IDE — the code is the demo |
| Metric Views missing | Show `02_metric_views.sql` and explain what it would create |
| Wrong query results | Say "even when Genie gets it wrong, we have a ground truth — let me show you the definition" |
| MCP server won't connect | Show the config JSON and walk through the 3 env vars — explain the architecture even if the live query fails |
| Agent returns wrong metric | Say "let me show you how we'd debug this" — use `get_model_details` to show the definition, then correct the query |
| App won't load | Use VS Code to walk through the files — the demo is the architecture |
