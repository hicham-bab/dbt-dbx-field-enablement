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

## Part 2: The 12 Competitive Concerns

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
genuinely good.

**Our response:** The scalability argument was always about the governance layer,
not just runtime reliability. The question isn't whether notebooks can run reliably
in production — it's whether stakeholders can review, test, and audit the business
logic that lives in them. A PySpark notebook with the revenue definition is not
reviewable by a business analyst. A SQL file with a YAML description is.

**Demo proof point:** Show `databricks/notebooks/01_lakeflow_pipeline.py` alongside
`platform/models/marts/fct_orders.sql`. Ask: "Which one can your CFO review in a PR?"

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

#### 7. Team lacks deep Databricks knowledge internally

**What they say:** "Your SAs don't know Databricks well enough to demo it credibly
alongside dbt."

**What is true:** This is a real gap for some dbt field teams. dbt SAs historically
focus on dbt, not on the Databricks platform.

**Our response:** This repo exists to close that gap. The Lakeflow pipeline in
`01_lakeflow_pipeline.py` is fully commented for dbt SAs to understand. The
`docs/architecture.md` explains the medallion architecture from a dbt-first perspective.
The honest answer is: we know dbt better than we know Databricks — which is exactly
why we can show where dbt adds value that Databricks's own tooling doesn't cover.

**Demo proof point:** Run the full 5-act demo. The credibility comes from knowing
BOTH systems well enough to compare them honestly.

---

#### 8. Enablement materials outdated

**What they say:** "The dbt + Databricks materials I've seen are outdated —
they reference old Databricks features or old dbt versions."

**What is true:** This was a real problem before this repo existed. Some older
enablement materials do reference dbt Core 1.5 patterns, old Unity Catalog behavior,
or pre-Genie workflows.

**Our response:** This repo is built for dbt Fusion (1.9+) and the current
Databricks platform (Unity Catalog, Genie, Lakeflow/DLT, Databricks Apps).
Every code file has been tested against current versions. The semantic layer
patterns use MetricFlow syntax. The Genie demo is against the current Genie API.

**Demo proof point:** Show the dbt Cloud job run for `platform/` — it uses the Fusion
compiler (Rust-based, dbt 1.9+), enforces `cast()` syntax, `arguments:` on all tests,
and no `config-version`. This is not demo scaffolding — it's a production-ready project.

---

#### 9. Governance: dbt beats DBX but hard for DBX sellers to accept

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

#### 10. Technical complexity: DBX remains highly technical despite marketing

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

#### 11. DBX SAs in France lack dbt knowledge

**What they say:** (Regional) "DBX SAs in France don't know dbt and actively
talk customers out of it."

**What is true:** Regional variation in competitive posture is real. Some local
Databricks teams have positioned against dbt without deep product knowledge.

**Our response:** Education is the answer, not confrontation. Offer to co-present
with Databricks SAs. Run this demo with them present. The 5-act structure shows
Lakeflow honestly — Databricks SAs will recognize and respect the fair treatment
of their product. The comparison only works because we're not dismissing Lakeflow.

**Demo proof point:** Act 3 specifically validates Lakeflow as "better than raw."
Databricks SAs will appreciate the honest acknowledgment of what Lakeflow does well.

---

#### 12. Migration effort vs greenfield opportunities

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
