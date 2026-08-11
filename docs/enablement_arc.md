---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
status: DRAFT - internal enablement only; needs PMM review before customer-facing reuse
reverify: quarterly
---

# The build-native-first enablement arc

## Why this design

The goal: have SA/SEs build everything in native Databricks first, hit the limits
themselves, then rebuild the same thing with Fivetran + dbt and measure the
difference.

That is better than a competitive deck, for a reason worth naming to the team:
**an SA who has personally hit the wall argues differently than one who memorized
a bullet.** They stop making claims and start telling stories. Stories survive
cross-examination from a Databricks SE. Claims don't.

It also inoculates them. Every SA will eventually meet a customer who has already
built the native version. If your team has built it too, they can say "yes, and
here's what happened at month four" instead of arguing with someone's completed
work.

## One caution before the design

The instinct is to say "with only Databricks native, the customer will struggle."
Adjust that by one degree.

Databricks native is genuinely good at several things. Unity Catalog RBAC is
excellent. Lakehouse Federation is excellent. Delta Sharing works. Metric views
now do joins, windowed measures, semi-additive measures and external agent
access. Declarative Automation Bundles are real IaC. An SA who walks in saying
"you'll struggle with native" to a customer currently succeeding with native has
lost before the second slide.

**Don't assert the struggle. Engineer the exercise so the customer discovers it.**
That is what build-native-first does, and it is strictly stronger: the finding
lands as *their* observation, and it's unarguable because they watched it happen.

Concretely, replace "customers struggle with Databricks native" with:

> **Native gets you to working fast, and to governed slowly.**

Defensible, true, and the actual shape of the data.

---

## The arc

Each stage is **build it natively → feel the limit → rebuild → measure the
delta.** The measurement is the deliverable.

### Stage 0 - Ingestion

| | Native | Fivetran + dbt |
|---|---|---|
| Build | Pick a source with no managed connector. Write the custom pipeline: auth, pagination, incremental state, error handling | Authorize, select tables, sync |
| Limit felt | It isn't done at the end of the session. And they own it forever | - |
| Measure | Hours to first row; lines of code owned | Minutes to first row; zero lines owned |

**The drift beat:** add a column at the source, re-sync both. Fivetran picks it up
automatically. Then immediately say *"and nothing here told you whether that
should change a metric."* That is the handoff into Stage 1, and it stops
ingestion looking like the whole story.

Full competitive detail: `docs/ingestion_battle_card.md`.

### Stage 1 - Transformation and testing

| | Native | dbt |
|---|---|---|
| Build | Lakeflow pipeline, bronze/silver/gold, expectations | Staging → intermediate → marts, tests, contracts |
| Limit felt | Expectations are three types. Documentation is inline comments. Nothing enforces a schema across pipelines | - |
| Measure | Lines of code per model; time to add a test; time to answer "what does this column mean" | |

### Stage 2 - Multi-team

**Highest-value stage. Give it the most time - half a day.**

Have participants build the *same* consumer logic three times (marketing,
finance, data science) natively. They will copy-paste. That's the point, and it
needs to be experienced rather than described.

| | Native | dbt Mesh |
|---|---|---|
| Build | Three pipelines reading shared gold tables via `spark.read.table()` | Three projects with `ref('platform','fct_orders')` and enforced contracts |
| Limit felt | Change a column in the producer. Nothing warns anyone. Downstream breaks at runtime, in someone else's team, later | Contract fails the build, in CI, on the PR |
| Measure | Time from breaking change to detection. Number of duplicated definitions | |

**The exercise that sells itself:** have one participant rename a column in the
producer while others work downstream. Let it break. Then do it again on the dbt
side and watch CI catch it before merge. Nobody argues with that afterwards.

Note the contract caveat on Databricks: names and order are enforced, **types are
not**, and a failed constraint leaves the bad table in place. Have participants
see that too, so they concede it accurately in front of customers.

### Stage 3 - Environments and CI

| | Native | dbt platform |
|---|---|---|
| Build | Declarative Automation Bundles, targets, GitHub Actions, per-developer schema isolation | Connect repo, enable CI |
| Limit felt | Per-PR isolated schemas and state-aware builds are both build-it-yourself | - |
| Measure | Setup time. Realistically 2-3 days on Databricks | |

Be careful here: bundles are genuinely strong IaC. The gap is PR-isolated schemas
and `state:modified+`, **not** "Databricks has no CI/CD". That overclaim is
called out in `NAMING.md` and the battle card, and it should not reappear here.

### Stage 4 - Metrics and semantics

| | Native | dbt |
|---|---|---|
| Build | Author a Unity Catalog metric view by hand | Define metrics in the project; optionally materialize as a UC metric view via dbt |
| Limit felt | Only the owner can edit. `ALTER VIEW` replaces the whole definition. No CI validation, breakage appears at runtime. `rely` join assertions are unvalidated and can silently return wrong numbers[^metric-views-rely-unvalidated] | PR, reviewer, git history, CI |
| Measure | Time to answer "who changed this definition and why" | |

**Do not run this stage as "metric views are weak".** They are not, any more. Run
it as *"same definition, two change-management models"* - see
`METRIC_VIEWS_COMPARISON.md`.

> **Blocker to resolve before running this with a group:** the `metric_view`
> materialization is **not available in Fusion** (dbt-core
> #15616),[^fusion-metric-view-unsupported] and this repo's demo leads with
> Fusion. Decide in advance which engine participants use for Stage 4 and put it
> in the runbook. Discovering this live, across a room, is a bad session.
> Requires dbt-databricks 1.12.2+ as a practical floor and DBR 16.4+.

### Stage 5 - Agent consumption

| | Native | dbt |
|---|---|---|
| Build | Genie on raw tables → Genie on gold → Genie on dbt-populated UC metadata | dbt MCP server against the Semantic Layer |
| Limit felt | Genie's answer quality tracks metadata quality exactly, and hand-authored Genie instructions live only in Genie - not in git, not reviewed | `list_metrics` returns the governed definition; `get_metrics_compiled_sql` shows the exact SQL |
| Measure | Answer accuracy across the three Genie Agents. Whether the reasoning is auditable | |

**Scope this stage correctly.** The limit being demonstrated is *metadata quality
and where context lives*. It is **not** "Databricks can't do agents" - Databricks
ships managed MCP servers and a Genie Conversation API, and agent access is
roughly at parity. Attacking it is a losing move and contradicts the metric views
guidance.

Genie reads Unity Catalog; **it never calls dbt**.[^genie-unity-catalog-only] The
corrected architecture is in `DEMO_SCRIPT.md` Act 4d.

---

## The scoreboard

Every participant fills this in with their own numbers. The filled-in sheet is
the enablement artifact, and it is more useful than any slide you could hand
them.

| Stage | Native: time | dbt+FT: time | Native: who maintains | Delta |
|---|---|---|---|---|
| 0 Ingestion | | | | |
| 1 Transform + test | | | | |
| 2 Multi-team | | | | |
| 3 Environments + CI | | | | |
| 4 Metrics | | | | |
| 5 Agents | | | | |

**Two rules, and they matter:**

1. **Real numbers only.** If native took 40 minutes because the participant
   already knew Spark, write 40 minutes. Inflated numbers get repeated to
   customers and then contradicted by the customer's own team.
2. **Record where native won.** It will win somewhere, probably PySpark
   ergonomics and streaming. An enablement doc that reports a clean sweep teaches
   the team to overclaim.

---

## Logistics gaps to close before running this

`CLASSROOM_SETUP.md` has good per-user isolation but is missing three things that
will hurt at this scale:

- **Cost guardrails.** Nothing about DBU budget, warehouse auto-stop or teardown.
  This arc doubles the compute footprint because everyone builds everything
  twice, and the repo already runs a generator job every 30 minutes
  indefinitely. Add auto-stop, a cluster policy and a teardown script first.
- **Timing.** No per-module durations. This arc is realistically **two days**,
  not an afternoon. Stage 2 alone needs half a day.
- **Genie Agent isolation.** Not in the isolation table, though each participant
  needs three. Check naming collisions and per-user creation permissions before
  the session.

---

## What to tell your SA/SEs on day one

> You are going to build everything twice. The native build is not a strawman and
> you should not sandbag it - build it as well as you can, because a customer's
> team will have built it that well.
>
> What you're measuring isn't whether Databricks works. It does. You're measuring
> what it costs to get from *working* to *governed*, and who pays that cost.
>
> When you're in front of a customer, you are not going to tell them Databricks
> is bad. You're going to tell them what happened when you built it yourself.
> That's a much harder thing to argue with.

---

<!-- BEGIN GENERATED SOURCES - edit sources.yml, then run scripts/build_citations.py -->

## Sources

Generated from `sources.yml`. Every claim about a competitor's capabilities cites one of these. Do not edit by hand.

[^fusion-metric-view-unsupported]: https://github.com/dbt-labs/dbt-core/issues/15616 (retrieved 2026-08-11)
[^genie-unity-catalog-only]: https://docs.databricks.com/aws/en/genie-agents/concepts (retrieved 2026-08-11)
[^metric-views-rely-unvalidated]: https://docs.databricks.com/aws/en/uc-semantics/metric-views/joins (retrieved 2026-08-11)

<!-- END GENERATED SOURCES -->
