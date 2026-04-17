# Deploying dbt on Databricks with Asset Bundles and CI/CD

A practical guide to deploying dbt transformations on Databricks using
infrastructure-as-code and automated CI/CD pipelines.

**Audience:** Data engineers, platform teams, SAs demoing production-grade deployment patterns
**Prerequisites:** Familiarity with dbt, Databricks, and Git-based workflows

---

## Why This Matters

Moving from manual deployments to automated, production-grade workflows is the
difference between a demo and a real data platform. This guide covers the integration
points and CI/CD implementation for deploying dbt projects on Databricks using
Databricks Asset Bundles (now called **Declarative Asset Bundles**) as the
infrastructure-as-code layer.

The reference architecture from this repo:

```
Raw Delta Tables  ->  dbt Fusion  ->  Tested Marts  ->  Semantic Layer  ->  Genie
                        |               |
                 Lakeflow DLT    dbt Mesh Consumers
                 (Bronze/Silver)  (marketing, finance, data_science)
```

This guide adds the **deployment layer** beneath that architecture:

```
Git Repository (GitHub/GitLab/Azure DevOps)
        |
        | Push / PR
        v
CI/CD Pipeline (GitHub Actions / Azure DevOps)
        |
        | databricks bundle deploy
        v
Databricks Workspace
  +-- Databricks Job (dbt tasks: deps -> seed -> run -> test)
  +-- SQL Warehouse (Serverless)
  +-- Unity Catalog (dev / prod catalogs)
```

---

## Part 1: Understanding Databricks Asset Bundles

### What Are Asset Bundles?

Databricks Asset Bundles (DABs) are the infrastructure-as-code solution for
Databricks. Think "Terraform for Databricks resources" -- but purpose-built
for the Databricks platform, with native understanding of Jobs, Pipelines,
SQL Warehouses, and dbt tasks.

A bundle defines:
- **What** resources to create (Jobs, Pipelines, Clusters)
- **Where** to deploy them (workspace, catalog, schema)
- **How** to configure them per environment (dev vs prod)

### Declarative Asset Bundles: The Evolution

As of 2025-2026, Databricks has rebranded and evolved Asset Bundles into
**Declarative Asset Bundles** (still using the `databricks bundle` CLI).
The key shift is philosophical and practical:

| Aspect | Classic DABs (pre-2025) | Declarative Asset Bundles (current) |
|---|---|---|
| **Configuration paradigm** | Imperative-leaning -- you specify resources and their exact configuration | Fully declarative -- you declare desired state, the system reconciles |
| **Resource management** | Manual resource lifecycle tracking | Automatic state tracking and drift detection |
| **Variable resolution** | Basic variable substitution | Rich expression language with conditionals and defaults |
| **Environment promotion** | Separate config files per target | Single config with target-aware overrides |
| **Permissions model** | Explicit permission blocks per resource | `run_as` and inherited permissions from targets |
| **Sync behavior** | Full upload on every deploy | Incremental sync -- only changed files are uploaded |
| **Validation** | Basic schema validation | Deep validation with workspace-aware checks (`bundle validate`) |
| **Dependency management** | Manual ordering via `depends_on` in jobs | Automatic dependency inference where possible |
| **CLI experience** | `databricks bundle deploy` | Same CLI, enhanced with `bundle summary`, `bundle run`, `bundle destroy` |

**What stayed the same:**
- The `databricks.yml` manifest file
- The `resources/` directory pattern
- Target-based environment management
- Integration with CI/CD via the Databricks CLI

**What improved:**
- **State tracking:** Declarative bundles maintain a deployment state, so
  `bundle deploy` only updates what changed -- not a full redeployment
- **Drift detection:** `bundle validate` can now detect when workspace
  resources have drifted from the declared state
- **Expression language:** Variables support `${if(...)}`, `${coalesce(...)}`,
  and other expressions for conditional configuration
- **Artifact management:** Better handling of large projects with `sync.exclude`
  patterns and incremental uploads

---

## Part 2: Bundle Structure for This Project

### Directory Layout

```
dbt-dbx-field-enablement/
+-- databricks.yml              # Main bundle configuration
+-- resources/
|   +-- dbt_job.yml             # dbt job definition (platform project)
+-- dbt_profiles/
|   +-- profiles.yml            # Profiles for bundle-deployed dbt runs
+-- .github/
|   +-- workflows/
|       +-- deploy-dbt.yml      # CI/CD pipeline (GitHub Actions)
+-- platform/                   # Producer dbt project (existing)
+-- marketing/                  # Consumer dbt project (existing)
+-- finance/                    # Consumer dbt project (existing)
+-- data_science/               # Consumer dbt project (existing)
+-- databricks/                 # Notebooks, Genie, App (existing)
+-- docs/                       # Documentation (you are here)
```

The bundle configuration lives at the repo root alongside the dbt projects.
This is intentional -- `databricks bundle deploy` uploads the dbt project
source code to the workspace, then the dbt task references it from there.

---

## Part 3: Core Integration -- Connecting dbt to Databricks

### Step 1: Configure Databricks Connection

The `dbt_profiles/profiles.yml` uses environment variables for security.
This file is used by the Databricks dbt task at runtime -- not by dbt Cloud.

```yaml
# dbt_profiles/profiles.yml
# Used by Databricks Asset Bundle dbt tasks
# Environment variables are injected by the bundle configuration

jaffle_shop:
  target: "{{ env_var('DBT_TARGET', 'dev') }}"
  outputs:
    dev:
      type: databricks
      catalog: dev
      schema: jaffle_shop
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "{{ env_var('DATABRICKS_HTTP_PATH') }}"
      # User-to-Machine OAuth authentication (interactive dev)
      auth_type: oauth
      threads: 4
      connect_retries: 3
      connect_timeout: 10
      retry_all: true

    prod:
      type: databricks
      catalog: prod
      schema: jaffle_shop
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "{{ env_var('DATABRICKS_HTTP_PATH') }}"
      # Machine-to-Machine OAuth authentication (CI/CD)
      auth_type: oauth-m2m
      client_id: "{{ env_var('DATABRICKS_CLIENT_ID') }}"
      client_secret: "{{ env_var('DATABRICKS_CLIENT_SECRET') }}"
      threads: 8
      connect_retries: 3
      connect_timeout: 10
      retry_all: true
```

**Key integration points:**

- **host:** Your Databricks workspace URL (no `https://`)
- **http_path:** SQL Warehouse or cluster connection path
- **OAuth:** User-to-Machine for dev (interactive), Machine-to-Machine for prod (automated)
- **catalog:** Unity Catalog namespace -- environment-specific (`dev` vs `prod`)

**How this differs from the existing `platform/profiles.yml`:**

The existing `platform/profiles.yml` in this repo uses PAT authentication
with `DBX_HOST`, `DBX_HTTP_PATH`, `DBX_TOKEN` environment variables.
That profile is for dbt Cloud or local CLI runs. The bundle profile uses
OAuth (recommended for production) and is consumed by the Databricks dbt
task running inside a Databricks Job.

### Step 2: When to Use Which Profile

| Deployment method | Profile file | Auth method | When to use |
|---|---|---|---|
| dbt Cloud (recommended for this demo) | Managed by dbt Cloud | OAuth / PAT | Full governance: Semantic Layer, Explorer, Mesh, CI/CD |
| Databricks Asset Bundle | `dbt_profiles/profiles.yml` | OAuth M2M | Self-managed deployment without dbt Cloud |
| Local CLI | `platform/profiles.yml` | PAT | Development and testing |

**Important:** Asset Bundles deploy dbt Core on Databricks compute. This means
you get execution but **not** the Semantic Layer, Explorer, managed CI/CD,
or Fusion compiler. See `BATTLE_CARD.md` Part 6 for the full comparison.
If your customer needs Genie with governed metrics, dbt Cloud is required.

---

## Part 4: Bundle Configuration

### The `databricks.yml` Manifest

This is the infrastructure-as-code manifest that defines what gets deployed:

```yaml
# databricks.yml
bundle:
  name: dbt_dbx_field_enablement

# Include all resource definitions
include:
  - resources/*.yml

# Workspace configuration
workspace:
  host: https://your-workspace.cloud.databricks.com

# Variables for environment-specific configuration
variables:
  warehouse_id:
    description: SQL Warehouse ID for dbt execution
  catalog:
    description: Unity Catalog name
  schema:
    description: Schema/database name

# Environment-specific targets
targets:
  # Development target
  dev:
    mode: development
    default: true
    workspace:
      root_path: ~/.bundle/${bundle.name}/${bundle.target}
    variables:
      warehouse_id: abc123def456       # Dev warehouse (2X-Small)
      catalog: enablement
      schema: ecommerce_dev_${workspace.current_user.short_name}

  # Production target
  prod:
    mode: production
    workspace:
      root_path: /Workspace/.bundles/${bundle.name}/${bundle.target}
    # Service principal for production -- never personal credentials
    run_as:
      service_principal_name: sp-dbt-production
    variables:
      warehouse_id: xyz789ghi012       # Prod warehouse (Medium)
      catalog: enablement
      schema: ecommerce

# Exclude unnecessary files from deployment
sync:
  exclude:
    - "*.csv"
    - "*.parquet"
    - "target/"
    - ".venv/"
    - "node_modules/"
    - ".git/"
    - "**/__pycache__"
    - "docs/"
    - "databricks/app/"
```

**Critical configuration elements:**

- **mode:** `development` vs `production` -- affects validation strictness
  and deployment behavior. Production mode requires `run_as`.
- **targets:** Environment-specific configurations. Variables are resolved
  at deploy time based on the active target.
- **run_as:** Service principal for production. Never use personal
  credentials in production. This is a security best practice and a
  requirement for audit compliance.
- **root_path:** Where bundle artifacts are deployed in the workspace.
  Dev uses the user's home directory; prod uses a shared workspace path.
- **sync.exclude:** Critical for performance. Large bundles (>100MB) slow
  down deployment. Exclude test artifacts, caches, and documentation.

---

## Part 5: Defining the dbt Job

### The `resources/dbt_job.yml`

This defines the Databricks Job that executes dbt commands:

```yaml
# resources/dbt_job.yml
resources:
  jobs:
    platform_dbt_job:
      name: "dbt platform build - ${bundle.target}"
      description: "dbt job to run platform transformations"

      # Job configuration
      max_concurrent_runs: 1
      timeout_seconds: 3600

      # Notifications
      email_notifications:
        on_failure:
          - ${workspace.current_user.userName}

      # Schedule (daily at 2 AM UTC)
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"
        timezone_id: "UTC"
        pause_status: UNPAUSED

      tasks:
        - task_key: dbt_deps
          description: "Install dbt packages"
          environment_key: serverless_dbt_env

          dbt_task:
            project_directory: ./platform
            profiles_directory: ./dbt_profiles
            commands:
              - "dbt deps"
            warehouse_id: ${var.warehouse_id}
            catalog: ${var.catalog}
            schema: ${var.schema}

        - task_key: dbt_seed
          description: "Load seed data"
          environment_key: serverless_dbt_env
          depends_on:
            - task_key: dbt_deps

          dbt_task:
            project_directory: ./platform
            profiles_directory: ./dbt_profiles
            commands:
              - "dbt seed"
            warehouse_id: ${var.warehouse_id}
            catalog: ${var.catalog}
            schema: ${var.schema}

        - task_key: dbt_run
          description: "Run dbt models"
          environment_key: serverless_dbt_env
          depends_on:
            - task_key: dbt_seed

          dbt_task:
            project_directory: ./platform
            profiles_directory: ./dbt_profiles
            commands:
              - "dbt run"
            warehouse_id: ${var.warehouse_id}
            catalog: ${var.catalog}
            schema: ${var.schema}

        - task_key: dbt_test
          description: "Test dbt models"
          environment_key: serverless_dbt_env
          depends_on:
            - task_key: dbt_run

          dbt_task:
            project_directory: ./platform
            profiles_directory: ./dbt_profiles
            commands:
              - "dbt test"
            warehouse_id: ${var.warehouse_id}
            catalog: ${var.catalog}
            schema: ${var.schema}

      # Serverless compute environment
      environments:
        - environment_key: serverless_dbt_env
          spec:
            dependencies:
              - dbt-core==1.10.15
              - dbt-databricks>=1.8.0,<2.0.0
```

**Job configuration highlights:**

- **Task dependencies:** `depends_on` ensures proper execution order:
  deps -> seed -> run -> test. If any task fails, downstream tasks are skipped.
- **Variable interpolation:** `${var.warehouse_id}` makes the job
  environment-aware. The same YAML deploys to dev or prod with different
  warehouses and catalogs.
- **Environment management:** The `environments` block installs dbt packages
  automatically. No need to pre-install dbt on the cluster.
- **SQL Warehouse execution:** Serverless compute means no cluster startup
  time. Pay per query second. Auto-scaling based on query load.

### Handling Python Models (data_science project)

SQL Warehouses cannot execute dbt Python models. For the `data_science`
project that includes PySpark models (`rfm_customer_features.py`,
`customer_churn_features.py`, `product_affinity_pairs.py`), use a hybrid
approach with a job cluster:

```yaml
# resources/dbt_data_science_job.yml (example)
resources:
  jobs:
    data_science_dbt_job:
      name: "dbt data_science build - ${bundle.target}"

      tasks:
        # SQL models on SQL Warehouse
        - task_key: dbt_staging
          dbt_task:
            project_directory: ./data_science
            profiles_directory: ./dbt_profiles
            commands: ["dbt run --select tag:sql"]
            warehouse_id: ${var.warehouse_id}

        # Python models on job cluster
        - task_key: dbt_python_models
          depends_on:
            - task_key: dbt_staging
          dbt_task:
            project_directory: ./data_science
            profiles_directory: ./dbt_profiles
            commands: ["dbt run --select tag:python"]
          job_cluster_key: python_cluster

      job_clusters:
        - job_cluster_key: python_cluster
          new_cluster:
            spark_version: "15.4.x-scala2.12"
            node_type_id: "i3.xlarge"
            num_workers: 2
```

---

## Part 6: CI/CD Pipeline Implementation

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-dbt.yml
name: Deploy dbt to Databricks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
  DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
  DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }}

jobs:
  validate:
    name: Validate Bundle
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        uses: databricks/setup-cli@main

      - name: Validate bundle configuration
        run: databricks bundle validate -t dev

  deploy-dev:
    name: Deploy to Dev
    needs: validate
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    environment: development
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        uses: databricks/setup-cli@main

      - name: Deploy to dev
        run: databricks bundle deploy -t dev

      - name: Run dbt build (dev)
        run: databricks bundle run -t dev platform_dbt_job

  deploy-prod:
    name: Deploy to Production
    needs: validate
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Install Databricks CLI
        uses: databricks/setup-cli@main

      - name: Deploy to production
        run: databricks bundle deploy -t prod

      - name: Trigger production dbt job
        run: databricks bundle run -t prod platform_dbt_job
```

**Pipeline design:**

- **PR triggers dev deployment:** Every pull request deploys to the dev target
  and runs the dbt build. Reviewers can verify the build passes before merging.
- **Merge to main triggers prod deployment:** Production deployments happen
  only on merge to main, with a required GitHub Environment approval gate.
- **`bundle validate` runs first:** Catches configuration errors (typos in
  resource names, missing variables, invalid YAML) before attempting deployment.
- **Service principal auth:** The `DATABRICKS_CLIENT_ID` and
  `DATABRICKS_CLIENT_SECRET` secrets authenticate via OAuth M2M. Never
  store PATs in CI/CD.

### Azure DevOps Pipeline (Alternative)

```yaml
# azure-pipelines.yml (for Azure DevOps customers)
trigger:
  branches:
    include: [main]

pr:
  branches:
    include: [main]

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: databricks-credentials

stages:
  - stage: Validate
    jobs:
      - job: ValidateBundle
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          - script: |
              curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
              databricks bundle validate -t dev
            env:
              DATABRICKS_HOST: $(DATABRICKS_HOST)
              DATABRICKS_CLIENT_ID: $(DATABRICKS_CLIENT_ID)
              DATABRICKS_CLIENT_SECRET: $(DATABRICKS_CLIENT_SECRET)

  - stage: DeployProd
    dependsOn: Validate
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProduction
        environment: production
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - script: |
                    curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
                    databricks bundle deploy -t prod
                    databricks bundle run -t prod platform_dbt_job
                  env:
                    DATABRICKS_HOST: $(DATABRICKS_HOST)
                    DATABRICKS_CLIENT_ID: $(DATABRICKS_CLIENT_ID)
                    DATABRICKS_CLIENT_SECRET: $(DATABRICKS_CLIENT_SECRET)
```

---

## Part 7: Detailed Comparison -- Classic DABs vs Declarative Asset Bundles

This section provides the side-by-side comparison for field conversations.

### 7.1 Naming Clarification

| Term | What it means |
|---|---|
| **Databricks Asset Bundles (DABs)** | The original IaC tool for Databricks, introduced in 2023. Used `databricks.yml` + `databricks bundle` CLI. |
| **Declarative Asset Bundles** | The current evolution of DABs (2025+). Same CLI, same manifest format, enhanced with state management, drift detection, and richer expressions. Databricks now uses this name to emphasize the declarative paradigm. |
| **Lakeflow Declarative Pipelines** | A separate concept. This is the declarative syntax for defining DLT/Lakeflow pipelines (SQL/Python). Not the same as Declarative Asset Bundles. Do not confuse them. |

### 7.2 Feature Comparison

| Feature | Classic DABs (pre-2025) | Declarative Asset Bundles (current) |
|---|---|---|
| **Bundle manifest** | `databricks.yml` | `databricks.yml` (same format, extended) |
| **CLI** | `databricks bundle deploy/validate/destroy` | Same commands + `bundle summary`, enhanced `bundle run` |
| **State management** | Stateless -- full redeployment every time | **Stateful** -- tracks deployed resources, incremental updates |
| **Drift detection** | None -- no awareness of manual workspace changes | **`bundle validate`** detects workspace drift from declared state |
| **Variable expressions** | Simple `${var.name}` substitution | Rich expressions: `${if(condition, then, else)}`, `${coalesce(...)}` |
| **Dynamic configuration** | Limited -- mostly static per target | Dynamic defaults based on workspace context (`${workspace.current_user}`) |
| **Sync performance** | Full file upload on every deploy | **Incremental sync** -- only changed files are uploaded |
| **Resource lifecycle** | Create/update. Destroy required manual cleanup. | Full lifecycle: create, update, **destroy** with dependency ordering |
| **Permission inheritance** | Explicit `permissions` blocks per resource | **`run_as`** at target level, inherited by all resources in that target |
| **Validation depth** | Schema validation only | **Workspace-aware validation** -- checks if referenced warehouses, clusters exist |
| **Multi-resource orchestration** | Manual dependency ordering | **Automatic dependency inference** for related resources |
| **Artifact management** | Upload everything in the project directory | `sync.exclude` with glob patterns, smart artifact handling |
| **Deployment environments** | Separate config files or complex overrides | Single `databricks.yml` with target-aware variable resolution |

### 7.3 What This Means for dbt Deployments

For dbt on Databricks specifically, the evolution from classic DABs to Declarative
Asset Bundles brings these practical improvements:

**1. Faster deployments:**
Incremental sync means only your changed dbt model files are uploaded on each
`bundle deploy`. For a project with 200 models, this turns a 30-second deploy
into a 3-second deploy after the initial upload.

**2. Environment parity:**
The enhanced variable system makes it trivial to configure dev/staging/prod
with a single `databricks.yml`. No more maintaining three separate config files
with subtle differences that cause "works in dev, breaks in prod" issues.

**3. Better validation:**
`bundle validate` now checks that your referenced SQL Warehouse exists and is
running, that the service principal has the right permissions, and that the
catalog/schema combination is valid. This catches errors at deploy time, not
at job runtime.

**4. Safe teardown:**
`bundle destroy` removes all resources created by the bundle in the correct
dependency order. No more orphaned jobs, stale file uploads, or zombie clusters
from failed deployments.

**5. Drift awareness:**
If someone manually modifies a deployed dbt job in the Databricks UI (changes
the schedule, adds a notification, modifies the warehouse), `bundle validate`
warns you that the workspace state has drifted from your code. This enforces
the IaC principle: the `databricks.yml` is the source of truth.

### 7.4 Migration Path

If you have an existing classic DABs setup, the migration to Declarative Asset
Bundles is straightforward:

1. **Update the Databricks CLI** to the latest version (0.230+)
2. **Run `bundle validate`** -- it will flag any deprecated syntax
3. **Replace explicit permissions** with `run_as` at the target level
4. **Add `sync.exclude`** patterns for files that don't need to be deployed
5. **Test with `bundle deploy -t dev`** -- behavior should be identical

No changes to `databricks.yml` structure are required. The manifest format is
backwards-compatible. The improvements are in the CLI behavior and deployment
engine, not in the config syntax.

---

## Part 8: Integration with dbt Cloud -- When to Use Which

This is the critical positioning question. Asset Bundles and dbt Cloud are
not competing solutions -- they operate at different layers.

### The Decision Matrix

| Requirement | Asset Bundles (self-managed) | dbt Cloud |
|---|---|---|
| Execute `dbt build` on Databricks | Yes | Yes |
| Infrastructure-as-code for job definitions | **Yes (native)** | Partial (API/Terraform) |
| CI/CD pipeline integration | **Yes (bundle deploy in any CI)** | Yes (native CI) |
| Semantic Layer JDBC endpoint | **No** | **Yes** |
| Genie queries governed metrics | **No** | **Yes** |
| dbt Explorer (searchable catalog) | **No** | **Yes** |
| Column-level lineage | **No** | **Yes** |
| dbt Mesh cross-project refs | **No** | **Yes** |
| Fusion compiler (10-40x faster) | **No** | **Yes** |
| Managed dev/staging/prod environments | Manual (via targets) | **Yes (native)** |
| Cost | Free (OSS CLI) + compute | License + compute |

### When Asset Bundles Are the Right Choice

- **Single-project deployments** without Mesh consumers
- **Teams already invested in Databricks Workflows** for all orchestration
- **No Semantic Layer requirement** -- BI tools query tables directly
- **Brownfield environments** where Databricks Jobs already manage the pipeline
- **Compliance requirements** that mandate self-managed infrastructure

### When dbt Cloud Is the Right Choice

- **Multi-project Mesh deployments** (this demo has 4 projects)
- **Genie integration** requiring governed metrics via the Semantic Layer
- **Multiple BI tools** (Tableau, PowerBI, Genie) needing consistent metrics
- **AI agent infrastructure** (dbt MCP server for governed analytics)
- **Large projects** (100+ models) benefiting from the Fusion compiler
- **Teams that value managed CI/CD** over building their own

### The Hybrid Pattern

Many production deployments use both:

```
Asset Bundles                    dbt Cloud
+-- Job scheduling               +-- Semantic Layer API
+-- Compute configuration        +-- Explorer + lineage
+-- Workspace resource mgmt      +-- Mesh cross-project refs
+-- CI/CD deployment trigger     +-- Managed environments
```

Asset Bundles handle the infrastructure layer (defining and deploying the
Databricks Job that triggers `dbt build`). dbt Cloud handles the governance
layer (Semantic Layer, Explorer, Mesh). The two coexist -- the Asset Bundle
job can trigger a dbt Cloud job via the API, or dbt Cloud can run
independently with its own scheduling.

---

## Part 9: Best Practices

### Security

- Use **service principals** for production -- never personal tokens or PATs
- Store secrets in your CI/CD platform (GitHub Secrets, Azure Key Vault)
- Implement **least privilege** -- grant only necessary permissions to the
  service principal
- Use **OAuth M2M** (Machine-to-Machine) for automated deployments, not PAT
- Rotate credentials regularly -- automate rotation where possible

### Infrastructure

- **Separate catalogs per environment** -- `dev`, `staging`, `prod` in
  Unity Catalog. This provides namespace isolation and fine-grained access control.
- **Use variables for all environment-specific config** -- warehouse IDs,
  catalog names, schema names. Never hardcode.
- **Right-size SQL Warehouses** -- 2X-Small for dev, Medium or larger for prod.
  Serverless is recommended for dbt workloads (no startup time, pay per query).
- **Exclude unnecessary files** from the bundle sync -- `target/`, `.venv/`,
  `.git/`, `docs/`. Large bundles slow down deployment.

### CI/CD Pipeline

- **Validate before deploy** -- `bundle validate` catches configuration errors
  before any resources are created or modified.
- **Use deployment environments** -- GitHub Environments or Azure DevOps
  Environments for approval gates on production deployments.
- **Send notifications** -- alert the team on deployment failures. Use the
  `email_notifications` block in the job definition.
- **Pin dbt versions** -- specify exact versions in the `environments.spec.dependencies`
  block to avoid surprise breakages from version upgrades.

### dbt-Specific

- **Separate `dbt deps` as its own task** -- if package installation fails,
  you want a clear signal, not a confusing error in `dbt run`.
- **Use `dbt build` instead of separate `dbt run` + `dbt test`** in most cases.
  `dbt build` runs models and tests in DAG order, catching failures earlier.
  The separated approach shown in this guide is for visibility in the Jobs UI.
- **Tag Python models** for hybrid SQL Warehouse + job cluster execution.
  SQL models run on the warehouse; Python models run on the cluster.

---

## Part 10: Common Limitations and Workarounds

### Limitation 1: Python Models on SQL Warehouses

**Issue:** SQL Warehouses cannot execute dbt Python models (PySpark).

**Workaround:** Use the hybrid approach described in Part 5 -- tag SQL and
Python models separately, run SQL models on the warehouse and Python models
on a job cluster.

### Limitation 2: Git Source Conflicts

**Issue:** Using `git_source` in job definitions conflicts with Asset Bundles.
The bundle deploys files to the workspace; `git_source` pulls from Git directly.

**Solution:** Let Asset Bundles handle deployment. Use relative workspace paths:

```yaml
# Do NOT use git_source with bundles
# git_source:
#   git_url: "https://github.com/org/repo"

# Use relative paths -- the bundle deploys the files
dbt_task:
  project_directory: ./platform
```

### Limitation 3: SQL Warehouse Auto-Creation

**Issue:** Asset Bundles don't create SQL Warehouses automatically. The
warehouse must exist before the job runs.

**Workaround:** Create warehouses via CLI in the CI/CD pipeline before deployment:

```bash
# In CI/CD pipeline, before bundle deploy
databricks sql-warehouses create \
  --name "dbt-warehouse-${ENVIRONMENT}" \
  --cluster-size "2X-Small" \
  --enable-serverless-compute \
  --auto-stop-mins 10
```

Or use Terraform for warehouse management alongside Asset Bundles for job management.

### Limitation 4: Bundle Size Limits

**Issue:** Large bundles (>100MB) slow down deployment significantly.

**Solution:** Use `sync.exclude` in `databricks.yml`:

```yaml
sync:
  exclude:
    - "*.csv"
    - "*.parquet"
    - "target/"
    - ".venv/"
    - "node_modules/"
    - ".git/"
    - "**/__pycache__"
    - "docs/"
    - "databricks/app/"
```

### Limitation 5: No Semantic Layer

**Issue:** Asset Bundles deploy dbt Core, not dbt Cloud. The Semantic Layer
JDBC endpoint is a dbt Cloud-only feature.

**Impact:** Genie cannot query governed metrics by name. BI tools cannot
hit a single metric endpoint. AI agents cannot use the dbt MCP server.

**Workaround:** There is no workaround. If you need the Semantic Layer,
you need dbt Cloud. Asset Bundles handle execution; dbt Cloud handles
governance. See Part 8 for the decision matrix.

---

## Part 11: Field Positioning -- The Deployment Conversation

### When a Customer Says "We'll Deploy dbt with Asset Bundles"

This is a valid choice for execution. Acknowledge it, then qualify:

> "Asset Bundles are excellent for deploying dbt jobs as infrastructure-as-code.
> You get version-controlled job definitions, environment-specific configuration,
> and CI/CD integration. That handles the deployment layer.
>
> The question is whether you also need the governance layer: the Semantic Layer
> for Genie, Explorer for discovery, Mesh for cross-team contracts. If yes,
> Asset Bundles handle deployment and dbt Cloud handles governance. They coexist."

### The Comparison to dbt Cloud Native CI/CD

| Aspect | Asset Bundles + GitHub Actions | dbt Cloud Native CI |
|---|---|---|
| PR environment isolation | Build it yourself (target per PR) | Built in (`dbt_pr_123_*` schemas) |
| State-aware builds | `state:modified+` requires manifest passing | Built in (deferred to production) |
| Deployment approval gates | GitHub Environments | dbt Cloud environment permissions |
| Job definition as code | `databricks.yml` (native) | dbt Cloud API / Terraform |
| Semantic Layer | Not available | Available |
| Effort to set up | 1-2 days | 2 hours |

### The Honest Recommendation

For this demo project specifically:

- **dbt Cloud** is the recommended deployment method (see `SETUP.md` Part D).
  It provides Mesh, Semantic Layer, Explorer, and Fusion -- all critical to
  the 5-act demo.

- **Asset Bundles** are the recommended method for customers who:
  - Have a single dbt project without Mesh consumers
  - Already manage all orchestration in Databricks Workflows
  - Don't need the Semantic Layer (no Genie, no multi-tool metrics)
  - Want full control over their deployment infrastructure

- **Both together** are for customers who want IaC for infrastructure
  (Asset Bundles) and governance for business logic (dbt Cloud).

---

## Quick Reference: Bundle CLI Commands

```bash
# Validate the bundle configuration
databricks bundle validate -t dev

# Deploy to the dev target
databricks bundle deploy -t dev

# Deploy to production
databricks bundle deploy -t prod

# Run a specific job
databricks bundle run -t dev platform_dbt_job

# View deployed resources
databricks bundle summary -t prod

# Tear down all resources in a target
databricks bundle destroy -t dev

# Check for workspace drift
databricks bundle validate -t prod
```

---

## Related Documentation

- `SETUP.md` -- Full environment setup (dbt Cloud path)
- `BATTLE_CARD.md` Part 6 -- Native dbt task vs dbt Platform comparison
- `BATTLE_CARD.md` Part 7 -- Databricks Jobs orchestrator deep dive
- `docs/architecture.md` -- Reference architecture diagrams
- `docs/fusion_cheat_sheet.md` -- dbt Fusion syntax rules
- `DEMO_SCRIPT.md` Act 4g -- dbt Platform vs Native dbt Task demo
