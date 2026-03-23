# dbt Mesh — AE-Friendly Explainer

## What is dbt Mesh? (30-second version)

dbt Mesh is a way to split a large dbt project into multiple smaller projects
that can safely reference each other. A central "platform" team owns the clean
data (customers, orders, products). Domain teams (finance, marketing, product)
build their own models on top — safely, with governance.

Think of it like an API contract between teams. The platform team publishes a
stable interface. Consumer teams build on it. If the platform team changes
the interface, the consumer team's build fails before it reaches production.

---

## Why Does It Matter? (For AEs)

### The problem it solves

Imagine a 50-person data team with one giant dbt project. Every team touches
the same files. Finance changes a revenue model that marketing depends on.
Marketing breaks. Nobody knows until a dashboard shows wrong numbers.

### What Mesh does

1. **Platform team** owns `dim_customers`, `fct_orders` — the core entities.
   They declare these models as `public` with a `contract`.

2. **Finance team** has their own dbt project. They reference the platform's
   `fct_orders` with `{{ ref('platform', 'fct_orders') }}`.

3. **If the platform team changes `fct_orders`** (removes a column, changes a type),
   the finance team's `dbt build` fails immediately — in CI, not in production.

### What this sounds like to a VP of Data

> "We have 8 data teams. They used to step on each other constantly.
> With dbt Mesh, the platform team owns the core models and the finance team
> owns their own models — but they're still connected. If the platform team
> breaks something, we catch it in CI before it reaches Tableau."

---

## The Three Key Concepts

### 1. Access Levels

Every model in dbt Mesh has an access level:

| Level | Meaning | Who can reference it |
|---|---|---|
| `private` | Internal only | Only models in the same project |
| `protected` (default) | Same-project or explicit consumers | Consumers who declare the project in `dependencies.yml` |
| `public` | Anyone | Any dbt project in the organization |

In this repo: staging and intermediate models are `protected`.
Mart models (`dim_customers`, `fct_orders`, `dim_products`) are `public`.

### 2. Contracts

A contract (`contract: enforced: true`) declares the expected schema:

```yaml
- name: dim_customers
  access: public
  config:
    contract:
      enforced: true
  columns:
    - name: customer_id
      data_type: integer
      constraints:
        - type: not_null
        - type: primary_key
```

If the platform team removes `customer_id` or changes it to `string`,
any downstream project that references `dim_customers` will fail at build time.
Not at runtime. At build time.

### 3. Cross-Project Refs

Consumer projects reference public models with a two-argument `ref()`:

```sql
-- In finance/models/fct_revenue.sql
select * from {{ ref('platform', 'fct_orders') }}
```

This tells dbt: "this model depends on the `fct_orders` model in the `platform` project."
dbt validates the dependency at compile time and enforces the contract.

---

## How to Demo It in 2 Minutes

1. **Open `finance/models/fct_revenue.sql`:**
   ```sql
   with orders as (
       select * from {{ ref('platform', 'fct_orders') }}
   )
   ```
   Say: "This is the finance team's model. It references the platform team's `fct_orders`."

2. **Open `platform/models/marts/_marts.yml`:**
   ```yaml
   - name: fct_orders
     access: public
     config:
       contract:
         enforced: true
   ```
   Say: "This is the platform team's contract. `access: public` means the finance team
   is allowed to reference it. `contract: enforced` means the schema cannot change
   without the finance team's build failing."

3. **The governance moment:**
   Say: "If I, as the platform team, change `fct_orders` and remove the `amount_paid`
   column, the next time finance runs `dbt build`, their build fails. Before any
   dashboard breaks. Before any stakeholder sees wrong numbers.
   That's governance enforced by the build system."

---

## Frequently Asked Questions

**Q: Do we need Mesh for small teams?**

No. dbt Mesh is most valuable for teams with multiple data consumers (5+ teams,
or teams in different business units). For a single team with a single dbt project,
standard dbt with `access: protected` is sufficient.

**Q: Does Mesh require dbt Cloud?**

Yes, for cross-project refs. The `{{ ref('platform', 'fct_orders') }}` calls in the
consumer projects are resolved via dbt Cloud's metadata service — which reads the
`platform` project's published manifest and enforces access tiers at compile time.
The `dependencies.yml` in `marketing/` and `finance/` declares this dependency.
Local CLI runs cannot resolve cross-project refs without the dbt Cloud metadata service.

**Q: How does Mesh relate to Unity Catalog data sharing?**

They solve different problems. Unity Catalog handles access control — who can
read which tables. dbt Mesh handles change management — when can the platform
team make breaking changes. You need both: UC for data access security,
Mesh for development governance.

**Q: What is the `groups.yml` file?**

Groups declare ownership. Each model belongs to a `group` with an owner (name + email).
This is used for documentation (the dbt docs site shows ownership) and for access
control (private models can only be referenced by models in the same group).

In this repo: platform models belong to `platform_core`, finance models belong to
`finance_analytics`, marketing models belong to `marketing_analytics`.
