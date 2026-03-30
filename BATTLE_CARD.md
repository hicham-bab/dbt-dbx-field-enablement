# dbt + Databricks — Field Battle Card

**For:** dbt SAs and AEs in conversations with Databricks customers and SAs
**Purpose:** Handle competitive concerns with factual, demo-backed responses

---

## Part 1: Positioning Framework

**The core message: AND, not OR.**

dbt and Databricks are complementary. Databricks provides the lakehouse infrastructure
(compute, storage, orchestration, streaming). dbt provides the business transformation
governance layer (testing, documentation, semantic metrics, CI/CD environments).

The customers who get the most value have both:
- Databricks for data ingestion, Lakeflow for Bronze/Silver pipelines
- dbt for the business transformation layer (Gold/Marts) and semantic layer
- Genie on top, powered by dbt's metadata

**The question to ask:** "What does your Genie Space look like today? Where do
the column descriptions come from — code or manual entry?"

---

## Part 2: The 9 Competitive Concerns

---

#### 1. Enhanced enterprise capabilities reducing dbt differentiation

**What they say:** "Databricks keeps adding enterprise features — Unity Catalog lineage,
DLT governance, Genie. Each release closes the gap with dbt."

**What is true:** Databricks is investing heavily in the governance and documentation
layer. Unity Catalog now supports table and column comments. Lakeflow has improved.

**Our response:** Databricks's enterprise features operate at the infrastructure layer
(access control, audit logs, physical lineage). dbt operates at the business logic
layer: version-controlled SQL, tested metrics, the semantic layer, and CI/CD environments.
These are complementary, not competing. UC column comments don't replace YAML-defined
business rules that are PR-reviewed and semantically typed.

**Demo proof point:** Show Act 4 — the `_semantic_models.yml` file with `return_rate`
as a ratio metric with an explicit description. Ask: "Where is this definition in
Unity Catalog or DLT?"

---

#### 2. Spark declarative pipelines sharing assets across catalog

**What they say:** "Spark + DLT can share assets across catalogs in Unity Catalog.
We have cross-catalog lineage. Why do we need dbt Mesh?"

**What is true:** Unity Catalog does provide cross-catalog data sharing and lineage.
DLT pipelines can read from multiple catalogs.

**Our response:** Cross-catalog data access is not the same as cross-project governance.
dbt Mesh adds contract enforcement (if the platform team changes a schema, consumer
builds fail immediately), access control at the model level (public/protected/private),
and version-controlled ownership declarations. UC lineage shows you that data flowed
somewhere — dbt Mesh governs whether it was allowed to change.

**Demo proof point:** Show `finance/models/fct_revenue.sql` using
`{{ ref('platform', 'fct_orders') }}` and `platform/models/marts/_marts.yml` with
`contract: enforced: true`. Explain what happens to the finance build if `fct_orders`
changes its schema.

---

#### 3. "Notebooks aren't scalable" argument weakening

**What they say:** "You used to say notebooks aren't scalable — but DLT has improved
so much that notebooks are now production-ready. The argument is outdated."

**What is true:** DLT pipelines running in notebooks are production-ready for
ingestion and ETL. The auto-lineage, retry logic, and expectation framework are
genuinely good. Notebooks CAN also add column descriptions to Unity Catalog via
`ALTER TABLE ... CHANGE COLUMN ... COMMENT '...'` or inline `CREATE TABLE` DDL —
this is a real capability, not a gap.

**Our response:** The scalability argument was never about runtime reliability or
even whether columns can be documented. It's about the governance workflow around
that documentation. A column comment added in a notebook cell is not version-controlled
alongside the transformation that produces the column, not tested for accuracy,
not PR-reviewed by the team that consumes the data, and not enforced by a schema
contract. It can drift silently the moment someone changes the model. dbt's
`persist_docs` pushes descriptions from the same YAML that defines the model's
contract and tests — they are co-located, co-reviewed, and co-deployed. The
difference is not capability, it's governance discipline at scale.

**Demo proof point:** Show `platform/models/marts/_marts.yml` — the column description
for `amount_paid` sits next to the `not_null` test and the `relationships` test
for the same column. They live, change, and ship together. Ask: "In your notebook
approach, how do you ensure the comment stays accurate when the transformation changes?"

---

#### 4. DBX customers are highly technical and want control

**What they say:** "Our customers are data engineers who prefer Python and PySpark.
They don't want another abstraction layer — they want control."

**What is true:** Many Databricks customers are highly technical and value control
over their pipeline code.

**Our response:** dbt doesn't take control away — it adds structure to the part
of the pipeline where structure is most valuable. Highly technical engineers can
still write complex SQL, use Python models, and control every transformation.
What dbt adds is testability, documentation, and the governance layer that
makes their work auditable by non-engineers. "Control" and "governance" are not
opposites.

**Demo proof point:** Show `platform/models/marts/fct_orders.sql` — plain SQL,
no magic. Then show `_marts.yml` — the contract. Ask: "Does this restrict what
the engineer can do? Or does it just make their work reviewable?"

---

#### 5. Less interest in self-service among DBX customer base

**What they say:** "Databricks customers are typically engineering-heavy. They don't
have the same self-service analytics pressure that, say, a Snowflake customer has."

**What is true:** Databricks historically attracts more engineering-heavy teams.
Self-service analytics adoption varies.

**Our response:** The trend is changing. Genie is Databricks's biggest bet on
business-user self-service. Every Databricks customer who deploys Genie has
the metadata quality problem — they just haven't solved it yet. dbt is the solution
to that problem. The more seriously Databricks customers take Genie, the more
they need dbt.

**Demo proof point:** Act 1 vs Act 4. Show what Genie looks like before and after
dbt. Ask: "Do your business users ask Genie questions today? What do they get?"

---

#### 6. DBX SAs believe their product supports less technical users

**What they say:** "Databricks SAs tell customers they don't need dbt —
Databricks handles the full stack for all users, technical and non-technical."

**What is true:** Databricks does have features for less technical users (Genie,
notebooks with autocomplete, SQL Editor). They genuinely believe their product
covers the full spectrum.

**Our response:** The test is: ask a business user to audit a Genie answer from
a Lakeflow-powered space. "Where does this revenue number come from? Who approved
this definition?" With Lakeflow alone, the answer is "read the PySpark notebook."
With dbt, the answer is "PR #47, reviewed by [name], definition in `_semantic_models.yml`."
That gap is real, regardless of what Databricks SAs say about it.

**Demo proof point:** The governance moment in Act 4 — `git log _semantic_models.yml`.

---

#### 7. Governance: dbt beats DBX but hard for DBX sellers to accept

**What they say:** (Internal) "DBX SAs know dbt wins on governance but they
don't want to admit it in front of customers."

**What is true:** This is accurate. Databricks's governance story is primarily
Unity Catalog (access control, audit logs, lineage). dbt's governance story
includes all of that plus: PR-reviewed definitions, contract enforcement,
test-gated deployments, and semantic layer versioning.

**Our response:** Don't make it adversarial. The message is "AND": UC governance
(who can access what) + dbt governance (what the data means and whether it changed).
Both are real, both are needed. Framing it as "dbt beats Databricks on governance"
will make Databricks SAs defensive. Framing it as "governance has two layers"
makes it a conversation.

**Demo proof point:** In the app, Tab 4 (Governance) shows both layers: UC permissions
(implied) and dbt contracts + PR audit trail (explicit).

---

#### 8. Technical complexity: DBX remains highly technical despite marketing

**What they say:** "Databricks markets itself as accessible to less technical users,
but in practice it's still a complex platform. Your customers struggle with it."

**What is true:** Databricks has a steep learning curve. The managed service
has improved but configuration is still complex.

**Our response:** This is an opportunity, not a problem. Complexity in the
platform layer is exactly where a structured, code-first tool like dbt adds value.
The more complex the underlying platform, the more important it is to have a
governance layer that makes the business logic readable and testable.

**Demo proof point:** Show `platform/models/staging/stg_customers.sql` —
5 lines of readable SQL. Then show `01_lakeflow_pipeline.py` — 100+ lines of
PySpark. Ask: "Which one can a new team member review on day one?"

---

#### 9. Migration effort vs greenfield opportunities

**What they say:** "Our customers are greenfield on Databricks. They're not
migrating from dbt — they're building from scratch. Why should they add dbt?"

**What is true:** Many Databricks customers are greenfield. The migration story
is less relevant for them.

**Our response:** The governance story is stronger for greenfield, not weaker.
Greenfield customers have the opportunity to build dbt governance into the stack
from day one — before they accumulate technical debt. The customers who added dbt
later spent months retrofitting documentation and tests. Starting with dbt means
starting with the governance layer that Genie needs to give accurate answers.

**Demo proof point:** Show the `platform/` project structure — clean, organized,
documented. "This is what 'starting right' looks like."

---

## Part 3: Quick-Reference Response Table

| If they say... | Respond with... |
|---|---|
| "We have DLT — why dbt?" | "DLT moves data. dbt makes it trustworthy. Show me your Genie column descriptions." |
| "Unity Catalog has lineage" | "UC has access-control lineage. dbt has business-logic lineage. Both are needed." |
| "Our team prefers Python" | "dbt SQL is reviewable by non-engineers. That's the point — governance that scales." |
| "Too many tools in the stack" | "One more YAML file per model. That's what governance costs. The alternative is manual maintenance." |
| "dbt is just another abstraction" | "It's structure, not abstraction. The SQL is still right there in the file." |
| "We don't need Mesh yet" | "When do you plan to have more than one team writing transformations?" |
| "Genie works fine on our Lakeflow tables" | "Great — open the Genie Space and ask it to audit the revenue number for you." |

---

## Part 4: Mutual Wins / Joint Value

When positioning dbt + Databricks together:

1. **Genie is better with dbt.** This is the clearest joint value — dbt's metadata
   makes Genie more accurate, consistent, and auditable. Frame dbt as a Genie accelerator.

2. **dbt Fusion is Databricks-optimized.** The Rust compiler was co-developed to run
   natively on Databricks. No `config-version`, `cast()` syntax, Unity Catalog-native.

3. **dbt uses Unity Catalog.** `persist_docs` pushes column descriptions from YAML
   into UC column metadata. dbt doesn't replace UC — it populates it.

4. **Databricks + dbt Cloud = enterprise data stack.** Orchestration (Databricks Workflows),
   governance (UC + dbt contracts), semantic layer (MetricFlow), AI/BI (Genie) —
   all components are complementary.

5. **The joint reference architecture:**
   - Lakeflow: Raw → Bronze → Silver (ingestion + streaming)
   - dbt: Silver → Gold/Marts (business logic + governance)
   - Semantic Layer: Metrics (Genie, BI tools)
   - UC: Access control + audit logs across all layers

---

## Part 5: Time to Value — The Three Deployment Patterns

This section is the most important one for conversations where a customer says
"we're already on Databricks, do we really need dbt Cloud?" or "we can just run
dbt Core ourselves." It reframes the question from *cost of adoption* to *cost of delay*.

---

### The Three Patterns

**Pattern 1 — Databricks Notebooks only**
The team builds pipelines directly in Databricks notebooks (Python/PySpark/SQL).
DLT manages orchestration and lineage. Unity Catalog manages access control.
No dbt in the stack.

**Pattern 2 — dbt Core self-hosted + Databricks**
The team runs open-source dbt Core, self-managed on their own infrastructure
(typically triggered by Airflow, Dagster, or Databricks Workflows). The dbt Cloud
IDE, environments, and Semantic Layer API are not part of the stack.

**Pattern 3 — dbt Platform (Cloud) + Databricks**
The team uses dbt Cloud with the full platform: managed IDE, CI/CD environments,
Explorer, the Semantic Layer API (MetricFlow), and native Databricks integration
(OAuth, Unity Catalog metadata push, Fusion compiler).

---

### Time-to-Value Comparison

The key distinction is between **time to first pipeline** (easy) and
**time to first trusted metric** (hard). The two are separated by weeks or months
depending on the pattern — and for AI use cases, only one pattern ever gets there.

| Milestone | Notebooks only | dbt Core + DBX | dbt Platform + DBX |
|---|---|---|---|
| First pipeline running | **Day 1** | Day 3–5 | Day 3–5 |
| First transformation under version control | Week 2+ (manual git) | Day 3 | Day 3 |
| First data quality test | Month 1+ (custom) | Week 1 | **Day 5** |
| First documented column (human-readable) | Month 2+ (manual) | Week 2 | **Day 5** |
| First CI/CD pipeline (dev → prod) | Never (manual deploy) | Month 1–2 | **Week 1** |
| Column descriptions in Unity Catalog | Yes (manual DDL, no version control) | Week 3 (scripted) | **Day 5** (`persist_docs`, co-located with tests) |
| Cross-team data contracts enforced | Never | Month 2–3 | **Week 2** (dbt Mesh) |
| Semantic metric queryable by name | **Never** | **Never** | **Week 2** |
| Genie giving governed, auditable answers | **Never** | **Never** | **Month 1** |
| AI agent querying a semantic layer | **Never** | **Never** | **Month 1** |
| New team member productive in < 1 week | Never | Rarely | **Yes** (Explorer) |

**The column that should end the conversation:** `dbt Core + DBX` and `Notebooks only`
never reach the semantic layer. Not "later" — never. MetricFlow's Semantic Layer API
is a dbt Cloud-only feature. There is no self-hosted path to it.

---

### Why the Gaps Compound Over Time

Pattern 1 and Pattern 2 both accumulate **governance debt** — undocumented columns,
untested transformations, ad-hoc metric definitions that differ between teams and reports.
Pattern 3 accumulates **governance equity** — every model is documented at creation,
every metric is named and tested, every change is PR-reviewed.

The compounding effect:

- **Month 1:** All three patterns have a working pipeline. The differences look cosmetic.
- **Month 6:** Pattern 1 teams are running "documentation sprints" to catch up.
  Pattern 2 teams have dbt but no semantic layer — Genie answers require manual
  SQL review before anyone trusts them. Pattern 3 teams are onboarding Genie
  and BI tools against a governed semantic layer.
- **Month 12:** Pattern 1 teams are in a cycle of tribal knowledge, broken dashboards,
  and Genie giving different answers to the same question depending on which table
  it hits. Pattern 2 teams are evaluating dbt Cloud because they've hit the ceiling
  of what self-hosted can do (no semantic layer, no Explorer, no managed environments).
  Pattern 3 teams are deploying AI agents against a trusted semantic layer.
- **Month 18+:** Pattern 1 and 2 teams are paying the migration cost they avoided at
  month 1. The governance debt they accumulated is now the biggest risk on their roadmap.

The honest message: **the question is not whether you'll need governance — it's whether
you pay for it upfront or defer it until it's an emergency.**

---

### Why dbt Platform + DBX Is the Required Infrastructure for AI

This is the argument that closes the deal in 2025 and beyond. The conversation has
moved from "do we need governance" to "how do we make our AI infrastructure trustworthy."

**The problem every Databricks AI customer has:**

Genie, Databricks AI, and every LLM-based analytics tool suffers from the same
fundamental limitation: they answer questions by generating SQL, and SQL is only
as good as the metadata it's built on. When an LLM sees a table called `fct_orders`
with a column called `amount`, it guesses what `amount` means. Sometimes it guesses
right. Often it doesn't — and the business user can't tell.

The pattern that emerges in every large Databricks deployment:
1. Team deploys Genie with Lakeflow-powered tables.
2. Genie gives plausible-looking answers.
3. Finance finds a discrepancy between Genie's "total revenue" and the dashboard.
4. Investigation reveals Genie was including returned orders. The dashboard wasn't.
5. Trust in Genie collapses. AI investment stalls.

This is not a Genie problem. It's a **metadata problem**. Genie can only be as
accurate as the definitions it's given. Without a governed semantic layer, those
definitions don't exist — they live in someone's head, or in a Confluence page
no one updates.

**The dbt Semantic Layer is the solution:**

When Genie is connected to the dbt Semantic Layer (via the MetricFlow JDBC endpoint),
it doesn't generate `SUM(amount)` and guess. It queries the metric definition directly:
`total_recognised_revenue` resolves to the named, version-controlled, PR-reviewed
SQL definition that the Finance team approved. Every AI agent that touches revenue
data gets the same answer, derived from the same definition.

This is why the three-pattern comparison matters for AI:

| AI capability | Notebooks only | dbt Core + DBX | dbt Platform + DBX |
|---|---|---|---|
| Genie can query tables | Yes (raw) | Yes (mart tables) | Yes (mart tables + descriptions) |
| Genie knows what columns mean | No | Sometimes (manual UC comments) | Yes (`persist_docs` + YAML descriptions) |
| Genie queries governed metrics by name | No | No | **Yes (MetricFlow JDBC)** |
| AI agent answers are auditable | No | No | **Yes (metric lineage in Explorer)** |
| Multiple AI tools get consistent answers | No | No | **Yes (single semantic layer)** |
| New metric available to all AI tools at once | Never | Never | **Yes (define once in YAML, serve everywhere)** |

**The "define once, serve everywhere" principle:**

This is the architectural argument that resonates most with engineering leaders.
With dbt Platform as the semantic layer, a metric defined in `_semantic_models.yml`
is immediately available to:
- Genie (via the Semantic Layer JDBC connection)
- Tableau and PowerBI (via the same JDBC endpoint)
- Python notebooks (via the `dbt-sl-sdk` Python client)
- Any AI agent or MCP server that queries the Semantic Layer API
- dbt Copilot and future dbt AI features

Without dbt Platform, each of these tools defines its own version of the metric.
You get five "total revenue" numbers that are all different. With dbt Platform,
you get one. The governance is defined in code, reviewed in a PR, and propagated
automatically to every consumer.

**The MCP / AI agent infrastructure angle:**

The emerging AI infrastructure pattern in 2025 is the **Model Context Protocol (MCP)**
— a standard interface that allows AI agents (Claude, GPT-4, Copilot) to query
external data systems using tools. dbt Cloud exposes an MCP server that allows
AI agents to:
- Browse the catalog of metrics and semantic models
- Query metrics by name with filters and time grains
- Get lineage information about how a metric is computed
- Understand which models and tests govern a metric

This means a company running dbt Platform + Databricks today is building the
AI infrastructure that will power their analytics agents tomorrow. The semantic
layer is not a nice-to-have — it's the **contract layer between humans and AI**.
Humans define what metrics mean. AI agents query that definition. Without the
contract layer, AI agents are guessing. With it, they're governed.

**The mandatory infrastructure argument:**

Ask the customer: "In two years, do you plan to have AI agents that can answer
business questions from your data?" The answer is always yes.

Then: "Those agents will need a source of truth for metric definitions. Where will
that come from?"

With Notebooks only or dbt Core: nowhere. The definitions will be scattered across
dashboards, notebooks, Confluence pages, and individual engineers' mental models.
Every agent will generate different SQL for the same question.

With dbt Platform: the Semantic Layer. One place. Version controlled. Auditable.
Available to every tool via a standard API.

This is why dbt Platform + Databricks is not just a better deployment pattern —
**it's the required infrastructure for any company that takes AI-powered analytics
seriously.**

---

### Handling the "dbt Core Is Good Enough" Objection

When a customer says "we can just run dbt Core ourselves and save on the dbt Cloud
license," acknowledge what's true and be direct about what's missing:

**What's true:** dbt Core handles transformations, tests, and documentation. For a
single team with simple deployment needs and no BI tool integration requirements,
it can work.

**What's missing:**

1. **The Semantic Layer API.** Not in dbt Core. Not available via self-hosting.
   A hard stop. If you need MetricFlow to serve Genie, Tableau, PowerBI, or any AI
   agent via JDBC, you need dbt Cloud. This alone closes the argument for any
   customer with Genie.

2. **Managed environments.** dbt Core has no concept of dev/staging/prod isolation
   managed for you. Teams build this themselves with Airflow, custom scripts, and
   environment variables. This takes weeks to set up and months to stabilize.

3. **Explorer and lineage UI.** dbt Core generates `manifest.json`. What you do
   with it is your problem. dbt Cloud Explorer gives you a searchable, lineage-aware
   catalog of every model, metric, and test in the project — without standing up
   infrastructure.

4. **dbt Fusion performance.** The Rust-based compiler in dbt Cloud is 10–40x faster
   than dbt Core's Python compiler on large projects. This matters in CI/CD pipelines
   where compile time directly affects developer velocity.

5. **Support and SLAs.** When the platform that governs your business metrics goes
   down, you want Tier 1 support, not Stack Overflow.

6. **dbt Copilot and future AI features.** All AI-assisted development features in
   dbt (column description generation, test generation, SQL suggestions) are
   Cloud-only. Self-hosting dbt Core opts you out of the roadmap.

**The honest framing:** dbt Core is the foundation. dbt Cloud is the platform.
The license cost buys the Semantic Layer API, managed environments, Explorer, Fusion
performance, support, and the AI roadmap. For a company that plans to use Genie
and build AI infrastructure on Databricks, the ROI calculation is straightforward:
the time saved on self-managed infrastructure + the cost of wrong Genie answers
from ungoverned metadata far exceeds the license cost in the first year.

---

## Part 6: The MVP Decision — Why the Native Databricks dbt Task Is a False Start

This is the section to use when a customer says: "We'll start with the native dbt
task in Databricks Jobs — it's free, it's built-in, and we just need something
working for the MVP. We'll evaluate dbt Cloud later."

The argument is not that the native task is broken. It works. The argument is that
it optimises for the wrong thing — it minimises week-one cost while maximising
month-three cost. By the time the customer realises what they're missing, they're
in the middle of a live project and the migration is disruptive.

---

### What the Native dbt Task Actually Is

Before the argument, be precise. The native Databricks dbt task ("Configure and run
dbt projects on Databricks") is **dbt Core running on Databricks compute**,
orchestrated by Databricks Jobs. It is not a reduced version of dbt Cloud. It is
a completely different product with a different ceiling:

| | Native dbt Task | dbt Platform (Cloud) |
|---|---|---|
| Executes dbt commands | Yes | Yes |
| Managed IDE with lineage | No | Yes (Cloud IDE) |
| CI/CD dev → staging → prod | Manual (job parameters) | Yes (managed environments) |
| `dbt docs` browseable as UI | No (raw JSON artifacts) | Yes (Explorer) |
| Column-level lineage | No | Yes |
| Data health tiles (test status per model) | No | Yes |
| Semantic Layer JDBC endpoint | **No** | **Yes** |
| Genie queries governed metrics by name | **No** | **Yes** |
| dbt Fusion (Rust compiler) | No | Yes |
| Support SLA | No | Yes |
| AI roadmap (Copilot, MCP server) | No | Yes |

The native task gives you the bottom row of that table — execution — and nothing above it.

---

### The MVP Timeline Where It Breaks

A typical Databricks MVP runs 6–8 weeks. Here is where the native dbt task fails, and
when, in the context of a real customer engagement:

**Week 1–2: Setup**
The native task looks fine. You connect a Git repo, point it at a SQL Warehouse,
write a `profiles.yml`, and run `dbt build`. It works. No visible difference yet.

Hidden cost already accumulating:
- No managed dev environment — each developer points at the same schema unless
  you manually set up per-user overrides in `profiles.yml` and pass `--target dev`
  in every run. One developer's test run overwrites another's.
- No CI/CD — every PR merge deploys to prod immediately unless someone builds
  a custom job-per-branch setup. This takes days to get right.
- The dbt Cloud IDE setup takes 2 hours. The native task equivalent (Git sync,
  custom compute, per-developer profiles, CI job) takes 2–3 days.

**Week 3–4: Building models**
Still fine. `dbt run`, `dbt test`, `dbt build` all work. `persist_docs` pushes
column descriptions to Unity Catalog. The team feels productive.

Hidden cost still accumulating:
- No Explorer means no one can browse the model graph, see what depends on what,
  or check which tests are failing across the project without reading raw JSON.
- Column-level lineage doesn't exist. When someone asks "where does `amount_paid`
  come from?", the answer is "read the SQL."
- Every `dbt docs generate` produces artifacts archived in the job run — not
  browseable, not shareable, not discoverable by the business.

**Week 5–6: Connecting Genie — the moment it breaks**

This is the demo week. The customer invites business users and leadership to see
Genie answer questions from the new mart tables. This is the MVP milestone that
justifies the project.

What happens:
1. The team adds `fct_orders`, `dim_customers`, `dim_products` to the Genie Space.
2. `persist_docs` has populated some UC column descriptions. Genie reads them.
3. A business user asks: **"What was total revenue last month?"**
4. Genie generates SQL. Without a Semantic Layer, it guesses. It might pick
   `SUM(amount)` from raw orders. Or `SUM(amount_paid)` including returned orders.
   Or it might get lucky and pick the right column this time and the wrong one next time.
5. The Finance lead asks: "Is this the same number as in our dashboard?"
6. It isn't. The dashboard excludes returned orders. Genie didn't know to.
7. Someone asks: "How do we make sure Genie always uses the right definition?"
8. The answer, with the native dbt task, is: **you can't.** There is no Semantic
   Layer. There is no named metric. There is no JDBC endpoint. Genie will always
   generate raw SQL from column descriptions, and it will always be inconsistent.

This is not a week-6 problem that can be fixed in week 7. It is an architectural
decision made in week 1 that cannot be resolved without migrating to dbt Cloud.

**The migration cost at week 6:**

If the customer decides to add dbt Cloud at this point, they are not doing a
"lift and shift." They are doing a rebuild:
- Reconnect the dbt Cloud project to the same Git repo (straightforward)
- Re-configure dev/staging/prod environments in dbt Cloud (1–2 days)
- Re-create all Databricks Jobs to point at dbt Cloud instead of the native task
- Add `_semantic_models.yml` with semantic models and metrics (1 sprint)
- Enable the Semantic Layer in dbt Cloud project settings
- Create service tokens and reconnect Genie to the JDBC endpoint
- Re-test all Genie queries against the new metric definitions
- Retrain business users on the new, consistent Genie answers

Estimated cost: **2–3 weeks of a data engineer + SA time**, in the middle of an
MVP that was supposed to demonstrate value to the business. Instead of celebrating
the MVP, the team is explaining why they need more time and budget.

---

### The Correct Framing for the Customer

Do not frame this as "the native task is bad." Frame it as a timing argument:

> "The native dbt task is a legitimate tool for teams that have no BI or AI
> ambitions — they just want transformations to run. But you're on Databricks,
> you're deploying Genie, and you're planning to use AI. The Semantic Layer is
> not an advanced feature you add later. It's the foundation that makes Genie
> trustworthy. Setting it up takes one afternoon in dbt Cloud. Migrating to it
> after the MVP takes two weeks. The question is when you want to pay that cost."

The conversation then becomes: **what does the Semantic Layer setup cost on day one?**

- Create a dbt Cloud project: 30 minutes
- Connect to Databricks via OAuth: 30 minutes
- Enable the Semantic Layer in project settings: 5 minutes
- Add `_semantic_models.yml` with 3 semantic models and 10 metrics: half a day
- Connect Genie via JDBC: 30 minutes

Total: **1 day.** The same day the team would have spent configuring the native
task's `profiles.yml`, CI job, and per-developer environment overrides — and still
not have the Semantic Layer at the end of it.

---

### The One Slide Version

If you need to put this in a deck, the message is three numbers:

| | Native dbt Task MVP | dbt Platform MVP |
|---|---|---|
| **Week-1 setup cost** | ~3 days (manual CI, profiles, environments) | ~1 day (managed) |
| **Week-6 Genie demo** | Inconsistent answers, no governed metrics | Governed metrics, auditable answers |
| **Migration cost if you switch at week 6** | 2–3 weeks rebuild | — |

Starting with the native task saves approximately **2 days** in week 1.
It costs approximately **2–3 weeks** in week 6 if you need the Semantic Layer —
which you do, the moment you connect Genie to your dbt models.

The MVP is not cheaper with the native task. It is deferred payment with interest.
