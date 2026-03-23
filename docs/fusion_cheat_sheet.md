# dbt Fusion — Syntax Rules and dbt Cloud Reference

## What is dbt Fusion?

dbt Fusion is the Rust-based compiler introduced in dbt 1.9. It runs inside dbt Cloud
on every job execution — you do not install it separately. All three projects in this
repo (`platform`, `marketing`, `finance`) are Fusion-conformant by design.

The Fusion compiler is stricter than the older Python-based compiler. The rules below
explain why the SQL and YAML in this repo look the way they do.

---

## Fusion Syntax Rules

### 1. No `::` casting — use `cast()`

```sql
-- WRONG (PostgreSQL syntax — Fusion rejects this)
select is_active::boolean from raw_products

-- CORRECT
select cast(is_active as boolean) from raw_products
```

### 2. No `config-version` in `dbt_project.yml`

```yaml
# WRONG
config-version: 2
name: platform

# CORRECT
name: platform
version: '1.0.0'
require-dbt-version: [">=1.9.0"]
```

### 3. `arguments:` key on all generic tests

```yaml
# WRONG (dbt Core syntax)
- accepted_values:
    values: ['placed', 'shipped', 'completed', 'returned']

# CORRECT (Fusion-conformant)
- accepted_values:
    arguments:
      values: ['placed', 'shipped', 'completed', 'returned']
```

This applies to all generic tests: `not_null`, `unique`, `relationships`,
`accepted_values`, and package tests like `dbt_utils` and `dbt_expectations`.

### 4. `require-dbt-version` is required

```yaml
require-dbt-version: [">=1.9.0"]
```

### 5. Explicit decimal precision for financial columns

```sql
-- Be explicit to avoid implicit type coercion issues
cast(0 as decimal(18, 2))
coalesce(amount, cast(0 as decimal(18, 2)))
```

---

## dbt Cloud: Job Commands

Each project has a deploy job with two commands:

```
dbt deps
dbt build
```

`dbt deps` installs `dbt_utils` and `dbt_expectations` from `packages.yml`.
`dbt build` runs all models and all tests in dependency order.

**Run order (required by Mesh):**
1. `platform - full build` job → must complete first
2. `marketing - full build` and `finance - full build` → can run in parallel after platform

**Other useful job commands (add as needed):**

| Command | When to use |
|---|---|
| `dbt build --select dim_customers+` | Rebuild one model and its dependents |
| `dbt build --select state:modified+` | Slim CI — only rebuild what changed |
| `dbt test` | Run tests without re-running models |
| `dbt source freshness` | Check staleness of all 5 raw sources |
| `dbt docs generate` | Regenerate the docs site artifact |

---

## dbt Cloud: Project Dependencies (Mesh)

Cross-project refs like `{{ ref('platform', 'fct_orders') }}` resolve via dbt Cloud's
metadata service. For this to work:

1. The `platform` project's Production environment must have **Generate docs on run** enabled
2. The `marketing` and `finance` projects must declare `platform` as a dependency:
   - Project settings → **Project dependencies** → Add → `platform`
3. Run `platform` first — the consumer jobs will fail if platform's published state is missing

The `dependencies.yml` in each consumer project declares this in code:
```yaml
projects:
  - name: platform
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| `config-version is not allowed` | Old `dbt_project.yml` syntax | Remove `config-version: 2` line |
| `Unexpected token ::` | PostgreSQL cast syntax | Change `col::type` to `cast(col as type)` |
| `arguments key is required` | Old generic test syntax | Wrap test params in `arguments:` |
| `Cross-project ref failed` | Platform published state missing | Re-run platform job with "Generate docs on run" enabled |
| `Contract violation` | Column type mismatch | Check `data_type:` in `_marts.yml` matches actual column type |
| `Profile not found` | Profile name mismatch | Ensure `profile:` in `dbt_project.yml` matches key in `profiles.yml` |

---

## Local Development (Optional)

The `profiles.yml` in each project supports local runs. Set three environment variables:

```bash
export DBX_HOST="your-workspace.azuredatabricks.net"
export DBX_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DBX_TOKEN="dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Then from the project directory:
```bash
dbt deps --profiles-dir .
dbt build --profiles-dir .
```

Note: **cross-project refs require dbt Cloud**. Running `marketing` or `finance`
locally will fail on `{{ ref('platform', ...) }}` because there is no local metadata
service to resolve the cross-project dependency.
