---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
status: DRAFT - needs PMM and competitive review before external use
reverify: quarterly, and after every Databricks DBR release
---

# Ingestion battle card: Lakeflow Connect vs Fivetran

## How to use this

This is the missing front half of the demo. Everything else in the repo starts at
"raw Delta tables already exist". This covers how they got there, and it is the
fight Databricks picks first.

**Read "What not to say" before you use anything else here.** Lakeflow Connect is
a real product that works. Sellers who claim it doesn't will lose the room.

---

## The one-line position

> Lakeflow Connect is good ingestion for a short list of sources you were probably
> going to build yourself anyway. Fivetran is the long tail, and the long tail is
> where the maintenance cost actually lives.

The corollary, which is the whole reason this section exists:

> Ingestion is not the point. The point is what you can do once the data lands.
> Databricks stops at "the table exists". We keep going: contracts, tests,
> lineage, metrics, and agent-consumable context.

---

## Why this fight is different now

Fivetran and dbt Labs completed their merger on **1 June 2026**. This is one
company.

- **Before:** "buy Fivetran for ingestion, then buy dbt for transformation" - two
  vendors, two procurement cycles, two renewals.
- **Now:** one vendor covering source-to-semantics, sitting on top of the
  customer's Databricks investment.

Databricks' strongest historical counter, "why add two vendors?", is now half as
strong. Use that.

**Caution, and this matters:** the *product* integration is still largely
roadmap. Fivetran Transformations hosts dbt Core and can orchestrate dbt platform
jobs as a third-party integration; Fivetran docs still carry a "not endorsed by
dbt Labs" disclaimer on those pages.

**Sell the company story. Do not sell a unified SKU that does not exist yet.** If
asked "is it one product", the honest answer is "one company, one roadmap,
integrated orchestration today, deeper integration coming - here's what ships
now."

---

## Fact base

Lakeflow Connect provides real managed connectors, but coverage is narrower than
Fivetran's and **GA status is uneven** - several database CDC connectors are
Preview and require account-team enrollment.[^lakeflow-connect-overview]

**Handle the connector-count point carefully - it is useful but not a knockout.**
Databricks' own FAQ answers "which connectors does Databricks support?" with a
short list, while the rest of the docs reference many more and link
connector-specific pages. A prepared Databricks SE will scroll and correct you
inside thirty seconds.

The defensible version:

> Their own FAQ leads with a handful while the docs list many more, and a good
> chunk needs account-team enrollment. That tells you maturity is uneven, which
> is fine for a young product. It just means the connector list isn't the
> question. The question is which of *your* sources are GA today.

On our side: **roughly three-quarters of Fivetran's application connectors carry
a "Lite" badge** - built for a specific use case, covering fewer endpoints. If
you quote a raw "hundreds vs dozens" number you will get this thrown back.

The honest framing: **a few hundred deep connectors plus a larger Lite tail,
against a Databricks list in the low dozens with uneven GA status.** That
comparison still wins comfortably and survives contact with a well-briefed
competitor. The inflated one does not.

> Don't put a precise Lite-vs-deep split on a slide. The counts shift as Fivetran
> ships, and Fivetran's own public numbers disagree with each other (700+ in
> docs, 750+ in marketing - **use "700+"**). "Roughly three-quarters" is accurate
> and safe.

---

## Fight 1: Connector breadth

**Their claim:** "We have managed connectors now. Ingestion is native to the
lakehouse."

**Your response:**

> Genuinely, the ones they've shipped work well. If those are your entire source
> landscape, Lakeflow Connect is a reasonable choice and I'd tell you so.
>
> Let's list your actual sources. For each one the question isn't "can Databricks
> ingest it" - it's "is there a managed connector, is it GA, and if not, who
> writes and maintains the pipeline?"

**Then let the list do the work.** Typical enterprise landscapes surface Marketo,
Braze, Coupa, Concur, Snowflake-as-a-source, mainframe extracts, regional payment
processors, and verticals like Veeva, Guidewire or Epic.

**The ladder Databricks documents for unsupported sources:**

1. Community connectors - open source, **explicitly not backed by Databricks
   SLAs**[^databricks-community-connectors-no-sla]
2. Custom connectors - you build and run them
3. Lakeflow pipelines / Structured Streaming - you build and run them
4. Auto Loader - cloud object storage only, so something else must land the files
5. Zerobus Ingest - direct push to Delta, but the source system must be modified
   to push
6. Lakehouse Federation - query in place, no ingestion

**The discovery question that lands:**

> "For the sources without a managed connector: who on your team owns that
> pipeline when the vendor changes their API? And what happens to that person's
> roadmap that quarter?"

---

## Fight 2: Schema drift

The strongest, most technical, most defensible ground here - and where you must
be precise, because both products are partly good and partly not.

### What Lakeflow Connect does

| Change | Behavior |
|---|---|
| New column | Auto-ingested next run; prior rows empty. Opt-out available |
| Deleted column | Not dropped - marked "inactive" via table property |
| Deleted column reappears with same name | **Pipeline fails.** Full refresh or manual drop required |
| New / deleted tables | Auto-handled when ingesting a whole schema |
| Data type change | **Not supported for Salesforce or SQL Server.** Oracle widening only |
| Column rename | Salesforce handles as drop+add. **SQL Server does not - full refresh** |

PostgreSQL DDL detection needs an "inline DDL tracking" preview feature that
installs event triggers and an audit table **inside the customer's Postgres**,
enabled via Databricks Support.

### What Fivetran does

- Diffs on every sync for new tables, new columns and type changes
- Type changes promote to the most specific type that losslessly accepts both
- Per-connection config: *Allow all* / *Allow new columns* / *Block all*
- Column-level blocking and hashing; soft-delete vs history mode per table
- Optional alerting on new schemas, tables and columns

### Our honest gaps - know these cold

A prepared Databricks SE will raise all four:

- **Narrowing type changes are silently ignored** - destination type isn't updated
- **Deleted source columns and tables are left behind** in the destination
- **Renames become add + drop**, for tables and columns
- **Primary key changes are not handled** - Fivetran's docs say you may see
  duplicates and recommend dropping and re-syncing, which costs MAR

**How to hold the line without overclaiming:**

> Neither product makes schema drift disappear. The difference is what happens on
> Tuesday morning when it hits.
>
> With Lakeflow Connect on a SQL Server source, a column rename means a full
> refresh. A dropped column that comes back fails the pipeline. A type change
> isn't supported at all.
>
> With Fivetran the type change is absorbed and promoted automatically, and you
> get an alert. Drift you don't want, you block at the connector.
>
> And here's the part that matters for this room: **absorbing drift is not the
> same as governing it.** Fivetran keeps the data flowing. What tells you a
> downstream metric just changed meaning is the dbt contract and the test.

That last paragraph is the bridge into the rest of the demo. Use it every time.

---

## Fight 3: Maintenance burden

**Their claim:** "It's serverless and managed. There's nothing to maintain."

**What the customer actually operates with database CDC:**

- **The CDC gateway can require customer-managed classic compute**, depending on
  the source. Databricks' FAQ says gateways can run in classic *or* serverless
  mode, so do **not** claim it's always classic. Where classic applies, the
  gateway runs continuously, is billed when the ingestion pipeline is idle, and
  cannot run in serverless-only workspaces. Check the specific source
- Postgres setup: `wal_level=logical`, replication user, publications, a
  replication slot per database, `REPLICA IDENTITY FULL` on tables without
  primary keys, and WAL tuning
- **Deleting a pipeline does not drop the replication slot** - drop it manually
  or risk WAL bloat
- **Deleting an ingestion pipeline drops the destination tables**
- If run N is still going when N+1 is scheduled, **N+1 is skipped**
- Per-connector table limits apply - **verify the current limit for the
  customer's specific connector; don't quote a figure from memory**
- OAuth U2M connectors **cannot be created programmatically** - interactive
  browser sign-in only, so there is no clean CI/CD path for them
- Databricks reserves the right to discontinue a connector if the upstream API
  changes

**The line:**

> "Serverless" describes the SaaS connectors. Database CDC runs a classic-compute
> gateway you size, monitor and pay for around the clock. That's not a criticism,
> it's how CDC works. Just don't budget for it as serverless.

**The strongest single maintenance argument:**

> Ask your team who fixed the last SaaS API breaking change, and how long it
> took. Then ask what else was on their roadmap that sprint. With Fivetran,
> connector upkeep is our problem under SLA. With a community or custom
> connector it's yours, and Databricks' docs say so
> explicitly.[^databricks-community-connectors-no-sla]

**Our honest gap:** Fivetran's Connector SDK shifts maintenance back to the
customer - you own the connector code, state handling, and fixes when the source
changes. A Connector SDK Maintenance offering exists; **check current commercial
terms with your account team before describing it.** Concede the ownership point
cleanly if asked; it applies only to sources we don't already cover.

---

## Fight 4: SaaS and app sources

Least contested ground, easiest win. Spend the least time here. Frame it as
roadmap risk, not feature count:

> The question isn't today's list - it's the third SaaS tool your marketing team
> buys next year without asking you. With us the answer is "it's already there,
> or it's a By Request build." Otherwise it's a data engineer's next two sprints.

---

## What not to say

Every item is either false or will be corrected in the room. This list protects
your credibility, which is the only asset you have in a competitive deal.

| Don't say | Why | Say instead |
|---|---|---|
| "Databricks can't do ingestion" | False. Lakeflow Connect is real and works | "It covers a short list well. Let's check yours against it." |
| Raw connector-count comparisons | ~3/4 of ours are Lite; you'll be corrected | "Hundreds of deep connectors plus a Lite tail, vs a list in the low dozens with uneven GA status" |
| "Databricks only has four connectors" | Their FAQ headline is narrow; the docs list many more. You'll be corrected on the page you're citing | "Their FAQ leads with a few and the docs list more. Maturity is uneven - which of *your* sources are GA?" |
| "The CDC gateway is always classic compute" | Their FAQ says classic **or** serverless depending on source | "Where classic applies it runs continuously and is billed when idle. Let's check your source." |
| "Fivetran handles all schema drift" | Narrowing ignored, deletes left behind, PK changes break | "Additive drift is automatic. Structural changes need governance downstream." |
| "Fivetran is cheaper" | MAR at scale is genuinely unpredictable | Never lead on price. Lead on time-to-value and maintenance load |
| "Databricks ingestion has no governance" | It lands directly in Unity Catalog with UC lineage | "It lands in UC. What it doesn't give you is contracts and tests on top." |
| Attacking the Fivetran-Databricks integration | Fivetran is 2025 Databricks Data Integration Partner of the Year | Lean on it - it's a proof point, not a liability |

---

## Objection handling

**"Why pay for a second tool when ingestion is included?"**

> It isn't included - it's metered in Lakeflow pipelines DBUs, plus a
> classic-compute gateway for database sources. So this isn't free versus paid,
> it's two paid approaches. The real comparison is which one covers your sources,
> and who maintains the ones it doesn't.

**"We want everything native to Unity Catalog for governance."**

> Fivetran writes Unity Catalog managed tables in Delta, supports UC volumes, and
> sets primary and foreign key constraints in UC. It's a Databricks-certified
> destination and was Databricks' 2025 Data Integration Partner of the Year.
> Native governance isn't the trade-off here.

**"We'll just build the connectors we need."**

> You can, and for one or two stable sources that's the right call. The cost
> isn't the build - it's that a data engineer now owns a vendor's API changes
> forever. Multiply by your source count.

**"MAR pricing is unpredictable and we've heard horror stories."**

> Fair, and I won't dismiss it - pricing moved to per-connection in March 2025,
> and deletes and history mode do count. Let's model your actual row volumes.
> What I'd push back on is comparing it to "free": the alternative is DBUs plus a
> continuously-running gateway plus engineering time.

**"Our Databricks rep says Lakeflow Connect covers us."**

> Great, let's make that concrete. Here's our source list. Which are GA today,
> which need account-team enrollment for preview, and which have no managed
> connector? Whatever's in that third bucket is the conversation.

---

## Discovery questions

Ask in this order. They build.

1. List every source system feeding the lakehouse today. How many?
2. Which are SaaS applications versus databases versus files or events?
3. Which are on a managed Databricks connector today, and GA versus preview?
4. Who wrote the pipelines for the rest? Are they still at the company?
5. When did a source API last change and break something? How long to fix?
6. How do you find out a source added a column - an alert, or a broken dashboard?
7. What's your CDC setup on the source databases, and who owns that config?
8. If you needed a new source live in production, what's the realistic timeline?

Question 8 sets up the demo. Write down their answer. You're going to beat it in
Act 0.

---

## Demo proof point: Act 0

Slots in before Act 1 and reinforces the build-native-then-rebuild structure in
`docs/enablement_arc.md`.

**Act 0a - Native (8 min).** Pick a source with no managed connector. Walk the
real path: check the connector list, find nothing, open the custom connector
docs, start writing a Python pipeline. Handle auth, pagination, incremental
state. **Do not finish.** Stop and say: "This is maybe two days to something
fragile, and I own it forever."

**Act 0b - Fivetran (4 min).** Same source. Authorize, select tables, sync. Show
the data landing in Unity Catalog as managed Delta with primary keys set.

**Act 0c - the drift moment (3 min).** Add a column at the source. Re-sync. It
appears. Then the line that carries the whole demo:

> That column arrived automatically, and that's exactly the problem we solve in
> the next act. Nothing here told you whether it should change a metric. The
> pipeline is healthy and your definitions are unguarded. That's what dbt
> contracts and tests are for.

**Timing on the slide:** use *your own* measured numbers, not illustrative ones.
Time the native attempt and the Fivetran sync yourself. A number you personally
measured survives challenge; one inherited from a battle card does not.

---

## Unverified - do not state as fact

Exact $/MAR rates by plan tier; precise current connector counts (Fivetran's own
materials conflict); the precise Lite-vs-deep split; GA versus preview status for
most individual Lakeflow SaaS connectors (rendered as UI badges that don't
survive text extraction); per-connector table limits; Lakeflow Connect DBU rates;
Connector SDK Maintenance commercial terms; any post-merger unified Fivetran +
dbt SKU.

**On the Databricks FAQ page:** Databricks revises these pages frequently. Open
the live page before you cite it. If you quote a "last updated" stamp that
doesn't match what the customer sees on screen, you lose the point regardless of
whether the underlying fact is right.

---

<!-- BEGIN GENERATED SOURCES - edit sources.yml, then run scripts/build_citations.py -->

## Sources

Generated from `sources.yml`. Every claim about a competitor's capabilities cites one of these. Do not edit by hand.

[^databricks-community-connectors-no-sla]: https://docs.databricks.com/aws/en/ingestion/community-connectors (retrieved 2026-08-11)
[^lakeflow-connect-overview]: https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/ (retrieved 2026-08-11)

<!-- END GENERATED SOURCES -->
