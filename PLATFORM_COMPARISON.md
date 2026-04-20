# dbt Cloud vs Databricks Native: Fair Platform Comparison

**Purpose:** Honest, structured comparison for field teams. For each topic, we state what Databricks does, what dbt Cloud does, what's a **real platform gap** vs what's just **"we didn't configure it"**, and where the two are complementary.

**Rule:** If Databricks can do something with reasonable configuration effort, say so. If it requires building custom infrastructure that dbt provides out of the box, say that too. Never claim a gap that's just a setup step.

---

## 1. Spark Declarative Pipelines (SDP) vs dbt Models

### What Databricks offers
Spark Declarative Pipelines (formerly Delta Live Tables / Lakeflow DLT) provide a declarative way to define data pipelines in SQL or Python. Key features:
- `CREATE OR REFRESH MATERIALIZED VIEW` / `CREATE OR REFRESH STREAMING TABLE` syntax
- Expectations (data quality constraints): `EXPECT`, `EXPECT OR DROP`, `EXPECT OR FAIL`
- Auto-lineage within a pipeline (visible in the DLT UI)
- Auto-retry and auto-scaling compute
- Streaming and batch in the same framework
- Lakeflow Designer (visual pipeline builder, preview)

### What dbt Cloud offers
- SQL or Python models (one model per file)
- `ref()` for compile-time dependency resolution
- 4 built-in tests + unlimited custom SQL tests + packages (dbt_expectations, etc.)
- `persist_docs` pushes descriptions to Unity Catalog
- Contracts (`enforced: true`) guarantee schema at compile time
- Semantic Layer (MetricFlow) serves named metrics via JDBC
- CI/CD with isolated PR environments
- Explorer with column-level lineage

### The honest comparison

| Dimension | SDP | dbt | Verdict |
|---|---|---|---|
| Streaming ingestion | **Strong** -- native streaming tables, auto-retry | Not designed for streaming | SDP wins for ingestion |
| Batch transformations | Works, but verbose in Python | **Strong** -- SQL-first, concise | dbt wins for business logic |
| Data quality checks | 3 expectation types (warn, drop, fail) | 4+ built-in tests, custom SQL, packages | dbt wins on depth and flexibility |
| Documentation | Inline comments in code only | YAML co-located with models, auto-generated docs site | dbt wins |
| Lineage | Within a single pipeline only | Across all projects (Explorer, column-level) | dbt wins on cross-project |
| Schema enforcement | None -- schema changes propagate silently | Contracts fail the build if schema changes | dbt wins |
| Python/PySpark support | **Native** -- first-class PySpark | Supported via Python models with `dbt.ref()` | Both work; SDP more natural for heavy PySpark |
| Metric definitions | Not supported | Semantic Layer (MetricFlow) | dbt only |
| Reusability across teams | Read via `spark.read.table()` (runtime) | `ref('project', 'model')` (compile-time, governed) | dbt wins on governance |

### Real gap vs didn't configure it

- **SDP lacks contracts** -- this is a **real platform gap**. There is no mechanism in SDP to enforce a schema across pipelines.
- **SDP lacks a Semantic Layer** -- **real gap**. No equivalent of MetricFlow JDBC.
- **SDP column descriptions** -- you CAN add them via `COMMENT` clauses or `ALTER TABLE`. This is a **configuration gap**, not a platform gap. But they're not version-controlled or PR-reviewed.
- **SDP lineage is limited to one pipeline** -- **real gap**. Cross-pipeline lineage exists in Unity Catalog but doesn't show transformation logic.

---

## 2. Git Integration Experience

### What Databricks offers
- **Databricks Repos (Git Folders):** Clone a Git repo into the workspace. Supports GitHub, GitLab, Azure DevOps, Bitbucket.
- **Branching:** Create/switch branches, commit, push, pull -- all from the UI.
- **Notebook editing:** Edit `.py`/`.sql` files directly in the workspace IDE. Notebooks saved as source files (not `.ipynb`).
- **Files in Repos:** Non-notebook files (YAML, configs) are visible and editable.
- **CI/CD:** Git changes can trigger Asset Bundle deployments via GitHub Actions or similar.

### What dbt Cloud offers
- **Native Git integration:** Connect GitHub/GitLab/Azure DevOps. Every project is a repo.
- **Cloud IDE:** Full development environment with file tree, SQL editor, lineage preview, `dbt build` in one click.
- **PR-based CI:** Every pull request automatically triggers a CI build in an isolated schema (`dbt_pr_123_*`).
- **Slim CI:** Only builds models affected by the PR (`state:modified+`).

### The honest comparison

| Dimension | Databricks | dbt Cloud | Verdict |
|---|---|---|---|
| Git clone and branch | Yes (Repos UI) | Yes (IDE + CLI) | Parity |
| Edit code in browser | Yes (workspace IDE) | Yes (Cloud IDE with lineage) | dbt Cloud IDE is more purpose-built |
| Commit, push, pull | Yes (basic UI, no merge/rebase) | Yes (full git operations) | dbt Cloud slightly better |
| PR triggers CI build | **Must configure yourself** (GitHub Actions + DABs) | **Built-in** (automatic) | dbt Cloud wins |
| Code review workflow | Use GitHub/GitLab natively | Use GitHub/GitLab natively | Parity |
| Notebook-specific merge conflicts | Can be painful (JSON cell conflicts) | N/A (plain SQL/YAML files) | dbt avoids the problem |

### Real gap vs didn't configure it

- **Databricks has git integration** -- this is NOT a gap. Repos work fine for version control.
- **PR-triggered CI is a configuration gap** -- Databricks CAN do this with GitHub Actions + DABs, but it's 1-2 days of setup vs dbt Cloud's zero-config CI. The lift is real but not prohibitive.
- **Merge conflicts in notebooks** -- **real friction point**. Notebook format (even as `.py` with `# COMMAND ----------` markers) creates harder merge conflicts than plain SQL files.

---

## 3. Production vs Development Separation

### Where do you see the production repo in Databricks?

**The short answer:** Production code lives in the Git repo (GitHub/GitLab). In Databricks, you see it in:
1. **Git Folders (Repos):** Each workspace user can clone the repo. Production branch is visible.
2. **Databricks Jobs:** Production jobs reference the repo + branch directly. The job definition shows which branch/commit is deployed.
3. **Asset Bundles:** If using DABs, `databricks bundle deploy -t prod` deploys from the repo to the production workspace path.
4. **Unity Catalog:** Production tables are in the production schema/catalog. You can inspect the data, but not the code that produced it, from the catalog.

**Can you inspect production code?**
- Yes, if you clone the production branch in a Git Folder.
- Yes, if you look at the Job definition (it references the repo and commit).
- No, there is no built-in "production code browser" -- you go to Git for that.

### Is production mixed with exploratory pipelines?

**This depends on how you configure it:**

| Approach | Separation quality | Effort |
|---|---|---|
| **Single workspace, no separation** | Bad -- exploratory notebooks sit next to production jobs | Zero effort, common default |
| **Workspace folders + naming conventions** | Moderate -- `/Production/` vs `/Exploratory/` folders | Low effort, discipline-dependent |
| **Separate catalogs** (`prod` vs `dev`) | Good -- Unity Catalog isolates data | Medium effort |
| **Separate workspaces** (`prod-workspace` vs `dev-workspace`) | Best -- full isolation | Higher effort, typical for enterprises |
| **Asset Bundles with targets** | Good -- `dev` and `prod` targets with different paths | Medium effort, code-driven |

### What dbt Cloud offers
- **Environments are built-in:** Dev, Staging, Prod -- each with its own schema, credentials, and job configuration.
- **Dev environment:** Each developer gets `dbt_<username>` schema automatically. No collision.
- **Production is code:** The production job runs from the main branch. You see exactly what's deployed in the Git repo.
- **Explorer:** Browse production models, their status, test results, and lineage. Production code is always inspectable.

### Real gap vs didn't configure it

- **Databricks CAN separate production from exploratory** -- this is a **configuration gap**. With separate catalogs, workspaces, or Asset Bundle targets, you get clean separation. But it requires intentional setup.
- **dbt Cloud has separation by default** -- this is a genuine advantage. No configuration needed.
- **"Where is the production code?" is harder in Databricks** -- **real friction**. You need to know which repo, branch, and commit a job uses. dbt Cloud's Explorer makes this one-click.

---

## 4. Modular / Reusable Pipelines

**The question:** Can you reuse an existing piece of script in Databricks?

### What Databricks offers

| Reuse mechanism | How it works | Limitations |
|---|---|---|
| **`%run` (notebook inclusion)** | Execute another notebook inline. Variables are shared. | Tight coupling. Hard to test. No dependency graph. |
| **Python libraries (wheels/packages)** | Package shared code as a Python library. Import in notebooks. | Requires packaging infrastructure (build, publish, version). |
| **Shared notebooks in Repos** | Import functions from `.py` files in the same repo. | Works within one repo. No cross-repo dependency management. |
| **DLT pipeline composition** | A DLT pipeline can include multiple notebooks. Each notebook contributes tables. | Within one pipeline only. No cross-pipeline reuse. |
| **Unity Catalog functions** | Register Python/SQL UDFs in UC. Callable from any notebook or query. | Good for scalar functions. Not for full transformations. |
| **Databricks Asset Bundles** | Define pipeline configurations in YAML. Parameterize with variables. | Infrastructure reuse, not logic reuse. |

### What dbt offers

| Reuse mechanism | How it works | Limitations |
|---|---|---|
| **`ref()`** | Reference any model. Compile-time resolved. DAG-aware. | dbt-specific. |
| **Macros** | Jinja functions reusable across models. | Can become complex. Learning curve. |
| **Packages** | Install community packages (`dbt_utils`, `dbt_expectations`). | Versioned dependency management built in. |
| **Cross-project refs (Mesh)** | `ref('platform', 'dim_customers')` -- governed reuse across projects. | Requires dbt Cloud for multi-project orchestration. |
| **Python models** | Write PySpark/Pandas with `dbt.ref()` for inputs. | Full language flexibility with governed dependencies. |

### The honest comparison

- **Databricks has reuse mechanisms** -- this is NOT a gap. `%run`, Python libraries, UC functions all work.
- **The gap is governed reuse** -- **real**. There is no equivalent of `ref()` that provides compile-time validation, lineage tracking, and contract enforcement. `spark.read.table()` works at runtime but doesn't validate at compile time.
- **Cross-project reuse is the biggest gap** -- **real**. dbt Mesh allows `ref('other_project', 'model')` with contract enforcement. Databricks has no equivalent. Teams read from shared tables via hardcoded strings with no governance.

### Real gap vs didn't configure it

- **Function-level reuse** (shared utility functions): **configuration gap** -- use Python packages or UC functions.
- **Model-level reuse** (reference a transformation from another project with governance): **real platform gap** -- no Databricks equivalent of Mesh refs.

---

## 5. CI/CD with Asset Bundles

**The question:** Is it a heavy lift to configure?

### What Databricks Asset Bundles (DABs) give you
- **Infrastructure as Code:** Define jobs, pipelines, clusters, and permissions in YAML.
- **Multi-target deployment:** `dev`, `staging`, `prod` targets with different configs.
- **CLI-driven:** `databricks bundle validate`, `deploy`, `run`.
- **GitHub Actions integration:** Trigger deploys on push/PR.
- **Dev mode:** Auto-prefixes job names with `[dev username]` to avoid collisions.

### How heavy is the lift?

| Task | Effort | What you get |
|---|---|---|
| Initial `databricks.yml` + `resources/*.yml` | **1-2 days** | Bundle config with dev/prod targets |
| GitHub Actions workflow for CI | **Half day** | `bundle validate` on PRs, `bundle deploy` on merge |
| dbt job definition in bundle | **1 hour** | dbt deps -> seed -> run -> test as a DABs job |
| Adding a new project/pipeline | **1-2 hours** | New resource YAML + target variables |
| Service principal for prod | **1-2 hours** | Secure, non-interactive deployment |

**Total initial setup: 2-3 days.** Ongoing maintenance is minimal -- you're editing YAML files.

### How this compares to dbt Cloud CI

| | DABs CI (Databricks) | dbt Cloud CI |
|---|---|---|
| Initial setup | 2-3 days (YAML + GitHub Actions) | **30 minutes** (connect repo, enable CI) |
| PR isolation (schema per PR) | **Build it yourself** (parameterize schema per PR) | **Built-in** (`dbt_pr_123_*`) |
| State-aware builds (only changed models) | **Not available** (full pipeline runs) | **Built-in** (`state:modified+`) |
| Cross-project dependency triggers | **Build it yourself** (job chaining) | **Built-in** (`dependencies.yml`) |
| Artifact management (manifest passing) | **Build it yourself** | **Built-in** |
| Dashboard of CI results | GitHub Actions logs | **Built-in** (Explorer, run history) |

### Real gap vs didn't configure it

- **DABs is genuinely powerful** -- not a gap. It's real IaC for Databricks resources.
- **DABs does not do PR-isolated schemas** -- **configuration gap** with significant effort. You CAN build this with parameterized schemas, but it's a day of engineering vs dbt Cloud's zero config.
- **DABs does not do state-aware builds** -- **real gap**. There is no `state:modified+` equivalent. Every deploy runs the full pipeline.
- **DABs + dbt Cloud work together** -- DABs handles infrastructure deployment; dbt Cloud handles the governance layer. This is the recommended hybrid pattern. See `docs/dabs_cicd_guide.md`.

---

## 6. Environment Management

**The question:** Is it a heavy lift to configure?

### How Databricks handles environments

| Approach | How it works | Effort | Quality |
|---|---|---|---|
| **Unity Catalog schemas** | `dev_schema`, `staging_schema`, `prod_schema` | Low | Good data isolation, shared compute |
| **Unity Catalog catalogs** | `dev_catalog`, `prod_catalog` | Medium | Better isolation, separate permissions |
| **Separate workspaces** | `dev.workspace.com`, `prod.workspace.com` | High | Full isolation, separate billing |
| **DABs targets** | `dev` and `prod` in `databricks.yml` | Medium | Code-driven, repeatable |
| **DLT pipeline settings** | Each pipeline has its own target catalog/schema | Low per pipeline | Good for pipeline isolation |

### How dbt Cloud handles environments
- **Built-in:** Dev, Staging, Prod environments created in the UI.
- **Dev:** Each developer gets `dbt_<username>` schema automatically.
- **CI:** Each PR gets `dbt_pr_<number>` schema automatically.
- **Prod:** Configured once, runs from main branch.
- **Credentials:** Per-environment, managed centrally.
- **Effort: 30 minutes** to set up all environments.

### The honest comparison

| | Databricks | dbt Cloud |
|---|---|---|
| Per-developer isolation | **Manual** (schema naming conventions or separate catalogs) | **Automatic** (`dbt_<username>`) |
| Per-PR isolation | **Build it yourself** | **Automatic** (`dbt_pr_<number>`) |
| Prod deployment | DABs `deploy -t prod` or manual job config | One-click from main branch |
| Environment switching | Change target/schema in config | Toggle in UI |
| Credentials management | Workspace tokens, service principals, secrets | Centralized in dbt Cloud |
| **Total setup effort** | **1-3 days** (depending on isolation level) | **30 minutes** |

### Real gap vs didn't configure it

- **Databricks CAN do multi-environment** -- **configuration gap**, not a platform gap. Unity Catalog provides the isolation primitives.
- **The lift is real but not prohibitive** -- 1-3 days for a solid setup. The ongoing maintenance is where it adds up (managing service principals, schema cleanup, CI job parameterization).
- **Per-developer and per-PR isolation is the hard part** -- **configuration gap with significant effort**. dbt Cloud provides this for free. Building it in Databricks requires custom scripting.

---

## 7. RBAC and Data Mesh

### Unity Catalog RBAC

Databricks Unity Catalog provides comprehensive RBAC:

| Level | Capability | Configuration effort |
|---|---|---|
| **Catalog** | `GRANT USE CATALOG` | Low |
| **Schema** | `GRANT USE SCHEMA`, `GRANT CREATE TABLE` | Low |
| **Table** | `GRANT SELECT`, `GRANT MODIFY` | Low |
| **Column** | Column masking, row filters | Medium |
| **Function** | `GRANT EXECUTE` | Low |

**This is NOT a gap.** Unity Catalog RBAC is mature and comprehensive. It handles *who can access what data*.

### dbt access control (different layer)

dbt adds a *model-level* access tier:

| Level | What it controls |
|---|---|
| `access: public` | Other projects can `ref()` this model |
| `access: protected` | Only models in the same project can `ref()` it |
| `access: private` | Only models in the same group can `ref()` it |
| `contract: enforced: true` | Schema is guaranteed -- downstream builds fail if it changes |
| `group:` | Ownership -- who is responsible for this model |

**The distinction:** UC RBAC controls *who can read a table*. dbt access tiers control *who can depend on a model at build time*. Both are needed. UC prevents unauthorized data access. dbt prevents unauthorized dependency coupling.

### How would you implement a Data Mesh?

**On Databricks (without dbt):**
1. Each domain team gets their own **catalog** or **schema** in Unity Catalog
2. Teams share data by granting `SELECT` on their gold tables
3. Cross-team dependencies are `spark.read.table("other_team.schema.table")` -- runtime only
4. No contract enforcement -- schema changes propagate silently
5. No dependency graph across teams -- each pipeline is isolated
6. Delta Sharing can share data across workspaces

**Effort:** Medium for basic isolation. But you have **no contract enforcement, no compile-time validation, and no cross-team lineage** linking producer and consumer pipelines.

**On dbt Cloud + Databricks (Mesh):**
1. Each domain team has their own **dbt Cloud project** targeting their own UC schema
2. Cross-project dependencies declared in `dependencies.yml`
3. `ref('platform', 'fct_orders')` -- compile-time validated, contract-enforced
4. `access: public/protected/private` controls who can reference what
5. `contract: enforced: true` guarantees schema stability
6. Explorer shows the full cross-project DAG

**Effort:** 1 day per consumer project to set up. Ongoing maintenance is YAML files.

### Real gap vs didn't configure it

- **UC RBAC is excellent** -- not a gap. Use it for data access control.
- **Cross-project governance is a real gap in Databricks** -- there is no native mechanism for contract enforcement or compile-time dependency validation across teams.
- **Delta Sharing handles cross-workspace data sharing** -- not a gap. But it shares data, not governance.

---

## 8. Cross-Instance Communication & Cross-Platform

### Can Databricks instances communicate with each other?

**Yes, via Delta Sharing:**
- Share tables across Databricks workspaces (even across clouds)
- Reader can query shared tables as if they were local
- Provider controls what's shared and who can access it
- Works across AWS, Azure, GCP
- **Effort:** Medium (set up sharing server, create shares, manage recipients)

**Also via Unity Catalog cross-workspace metastore:**
- A single UC metastore can serve multiple workspaces
- All workspaces see the same catalogs, schemas, tables
- **Effort:** Low if workspaces share a metastore. Higher if federated.

### Do they have a cross-platform story?

**Yes, via Lakehouse Federation:**

| External source | Support | How it works |
|---|---|---|
| **Snowflake** | Yes | Create a connection + foreign catalog. Query Snowflake tables as `snowflake_catalog.schema.table`. |
| **PostgreSQL** | Yes | Same pattern. Federated queries. |
| **MySQL** | Yes | Same pattern. |
| **SQL Server** | Yes | Same pattern. |
| **BigQuery** | Yes | Same pattern. |
| **Redshift** | Yes | Same pattern. |
| **Custom JDBC** | Yes | Any JDBC source via generic connection. |

**How it works:**
```sql
-- Create a connection to Snowflake
CREATE CONNECTION snowflake_conn
TYPE snowflake
OPTIONS (
  host 'account.snowflakecomputing.com',
  user 'service_user',
  password secret('scope', 'key')
);

-- Create a foreign catalog
CREATE FOREIGN CATALOG snowflake_data
USING CONNECTION snowflake_conn;

-- Query it like a local table
SELECT * FROM snowflake_data.schema.table;
```

**Effort:** Low per connection. Medium for governance (federated tables don't have the same lineage depth as native Delta tables).

### How dbt handles cross-platform

dbt doesn't directly query across platforms in a single project. Instead:
- Each project targets one data platform (Databricks, Snowflake, etc.)
- Cross-platform data movement happens at the infrastructure layer (Lakehouse Federation, Fivetran, etc.)
- dbt Cloud Explorer shows lineage within and across dbt projects, but not external sources

### Real gap vs didn't configure it

- **Cross-instance communication is NOT a gap** -- Delta Sharing and shared metastores work well.
- **Cross-platform (Snowflake querying) is NOT a gap** -- Lakehouse Federation is production-ready.
- **Cross-platform lineage is a gap on both sides** -- neither Databricks nor dbt tracks full lineage across platforms (e.g., from Snowflake source through Databricks transformation to dbt mart). This is an industry-wide gap.

---

## 9. Summary: The Honest Scorecard

| Topic | Databricks native | dbt Cloud | Winner | Notes |
|---|---|---|---|---|
| Streaming ingestion | **Strong** | Not applicable | Databricks | dbt is not for streaming |
| Batch transformations (SQL) | Adequate | **Strong** | dbt | SQL-first, concise, ref() |
| PySpark transformations | **Strong** | Good (Python models) | Databricks (slight) | Both work; DBX more natural |
| Data quality tests | Basic (3 types) | **Strong** (4+ types, packages, custom) | dbt | Depth and flexibility |
| Git integration | Good (Repos) | Good (IDE) | Tie | Both work |
| PR-based CI | Build it yourself (1-2 days) | **Built-in** | dbt Cloud | Real effort difference |
| Environment management | Build it yourself (1-3 days) | **Built-in** (30 min) | dbt Cloud | Real effort difference |
| RBAC (data access) | **Strong** (Unity Catalog) | N/A (uses UC) | Databricks | UC is excellent |
| Model-level access control | None | **Strong** (public/protected/private) | dbt | Real gap |
| Schema contracts | None | **Strong** (enforced contracts) | dbt | Real gap |
| Semantic Layer / metrics | None | **Strong** (MetricFlow JDBC) | dbt | Real gap |
| Cross-project governance | None | **Strong** (Mesh, refs, contracts) | dbt | Real gap |
| Cross-instance data sharing | **Strong** (Delta Sharing) | N/A | Databricks | Good feature |
| Cross-platform queries | **Strong** (Lakehouse Federation) | N/A | Databricks | Good feature |
| Documentation & metadata | Manual (UC comments) | **Strong** (YAML, persist_docs) | dbt | Governance difference |
| Lineage (within project) | Good (DLT UI) | **Strong** (Explorer, column-level) | dbt | Depth difference |
| Lineage (cross-project) | Basic (UC catalog-level) | **Strong** (Explorer, Mesh) | dbt | Real gap |
| Modular reuse (within project) | Good (%run, packages) | **Strong** (ref, macros, packages) | dbt | Governed reuse |
| Modular reuse (cross-project) | Runtime only (spark.read.table) | **Strong** (Mesh refs, contracts) | dbt | Real gap |
| Production visibility | Requires navigation to Jobs/Git | **Strong** (Explorer, one-click) | dbt Cloud | Friction difference |
| DABs / IaC | **Strong** | N/A (uses DABs for infra) | Databricks | DABs is good |

### The pattern

- **Databricks wins** on: infrastructure, streaming, RBAC, cross-platform, compute
- **dbt Cloud wins** on: governance, contracts, semantic layer, CI/CD, documentation, cross-project
- **They're complementary** on: the recommended architecture is Databricks for infrastructure + dbt Cloud for governance

### The "real gap" vs "didn't configure it" cheat sheet

| Claimed gap | Reality |
|---|---|
| "Databricks has no CI/CD" | **Didn't configure it** -- DABs + GitHub Actions works. But more effort than dbt Cloud. |
| "Databricks has no environment management" | **Didn't configure it** -- UC schemas + DABs targets. More effort. |
| "Databricks has no git integration" | **Wrong** -- Repos works fine. |
| "Databricks can't document columns" | **Wrong** -- `COMMENT` clauses work. But not version-controlled or PR-reviewed. |
| "Databricks has no schema contracts" | **Real gap** -- nothing prevents silent schema changes across pipelines. |
| "Databricks has no Semantic Layer" | **Real gap** -- no MetricFlow equivalent, no JDBC metric endpoint. |
| "Databricks has no cross-project governance" | **Real gap** -- no Mesh refs, no compile-time validation across teams. |
| "Databricks has no modular reuse" | **Wrong** -- %run, packages, UC functions all work. But no governed cross-project reuse. |
| "Databricks can't query external sources" | **Wrong** -- Lakehouse Federation is excellent. |
| "Databricks instances can't communicate" | **Wrong** -- Delta Sharing and shared metastores work. |

---

## 10. Demo Talking Points

When running the demo, use these to address each question naturally:

**"Show me git integration"**
> Open Databricks Repos. Clone the repo, switch branches, show the file tree. Then show: "Now look at dbt Cloud IDE -- same repo, but with lineage preview, inline test results, and one-click `dbt build`. Both have git. dbt Cloud has governance on top."

**"Where is production code?"**
> "In Git -- same as any software project. In Databricks, production code runs via Jobs referencing the main branch. In dbt Cloud, production is visible in Explorer: every model, its status, its test results, its lineage. The difference is discoverability."

**"Can you build modular pipelines?"**
> "In Databricks: yes -- use Python packages, `%run`, or UC functions for shared utilities. In dbt: `ref()` for governed dependencies, macros for shared logic, packages for community libraries. The gap is not 'can you reuse code' -- it's 'can you govern the reuse.' `spark.read.table()` works but doesn't validate. `ref()` validates at compile time."

**"How heavy is CI with Asset Bundles?"**
> "Initial setup: 2-3 days. Ongoing: editing YAML. It's real IaC -- genuinely good. But it doesn't give you PR-isolated schemas or state-aware builds. Those require dbt Cloud or custom engineering."

**"How does RBAC work? Can you do Data Mesh?"**
> "Unity Catalog RBAC is excellent for data access control. For Data Mesh governance -- contracts, access tiers, cross-project lineage -- you need dbt Mesh. UC controls who can read the data. dbt Mesh controls who can depend on the model and guarantees the schema won't change without failing builds."

**"Can Databricks talk to Snowflake?"**
> "Yes. Lakehouse Federation lets you query Snowflake (and Postgres, BigQuery, Redshift, etc.) as if it were a local table. `SELECT * FROM snowflake_catalog.schema.table`. Production-ready, low setup effort."
