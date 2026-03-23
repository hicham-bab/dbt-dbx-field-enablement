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
| 4 | dbt + Semantic Layer: The Solution | 8 min | Genie on dbt marts — accuracy, consistency, governance |
| 5 | Business Close | 3 min | The "AND not OR" message + next steps |

---

## Pre-Session Checklist

Complete at least 30 minutes before the demo:

- [ ] `00_setup_raw_data.py` has run — all 5 raw tables exist in `enablement.ecommerce`
- [ ] `01_lakeflow_pipeline.py` has run — 13 Lakeflow tables in `enablement.ecommerce_lakeflow`
- [ ] `04_lakeflow_mesh_equivalent.py` has run — marketing + finance Lakeflow tables exist (contrast demo)
- [ ] dbt Cloud `platform - full build` job is green — all 3 mart tables built, all tests pass
- [ ] dbt Cloud `marketing` and `finance` jobs are green — consumer models built
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

## Act 3: Lakeflow Gold — Better But Not Enough (5 min)

**Goal:** Show that Lakeflow alone improves Genie but doesn't solve the governance problem.

**Open:** Genie Space `E-Commerce (Lakeflow Gold — Act 3)`

**Run the same questions as Act 1:**

1. *"What was total revenue last month?"*
   - Better — Genie finds `daily_revenue` in `gold_fct_revenue`
   - **Say:** "Better. Lakeflow gold has cleaner structure. But the definition
     of `daily_revenue` lives in a Python DLT notebook. The instruction I wrote
     manually says 'completed orders only' — but I had to write that. If the
     pipeline changes, I have to remember to update these instructions too."

2. *"Show me revenue by customer segment"*
   - Works — but only because you wrote the instructions manually
   - **Say:** "This works now. But notice why: I wrote the segment definition
     manually in the Genie Space instructions. This isn't connected to the code.
     If a developer changes the segmentation logic in the DLT notebook,
     these instructions don't update automatically."

3. *"What is our return rate?"*
   - Closer — but ratio definition still manual
   - **Say:** "Still no formal definition of this ratio. Still guessing."

**The key moment — show the Genie Space instructions:**

> "Here is the Genie instruction I wrote manually for Lakeflow. Notice it took me
> 10 minutes to write. It has no connection to the DLT code. If the code changes,
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

### Part 4d: Complexity (1 min)

Show the semantic layer in `_semantic_models.yml`:
- Point to `return_rate` ratio metric
- Point to `revenue_per_customer` derived metric

**Say:** "Derived metrics. Ratio metrics. Time-grain-aware metrics. These aren't
just SQL views — they're named calculations with descriptions that Genie reads.
The same definition powers Tableau, PowerBI, Genie, and this dashboard."

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
> Genie instructions, manually writing column descriptions, and hoping the DLT
> notebook stays in sync with the documentation. dbt automates all of that."

**"Our team is Python-native, not SQL."**
> "dbt supports Python models. And the SQL in dbt models is readable by any analyst
> or stakeholder. That's the point — business logic that anyone on the team can read
> and review, not just the engineer who wrote it."

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
| App won't load | Use VS Code to walk through the files — the demo is the architecture |
