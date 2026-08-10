---
version: 1.0
last_verified: 2026-08-11
expires: 2026-11-09
owner: hicham-bab
---

# Ingest: Salesforce → Managed Data Lake Service → Unity Catalog

The front of the loop. A Fivetran Salesforce connector lands data through the
**Managed Data Lake Service (MDLS)** as open Delta/Iceberg tables, registered in
**Unity Catalog** so dbt (and Genie) treat them as first-class governed tables.

## What you get

- Standard Salesforce objects (`account`, `contact`, `opportunity`, `user`, …) landed
  as **Delta + Iceberg** over the same Parquet in your object storage.
- Fivetran manages normalization, compaction, dedup, schema drift - no maintenance jobs.
- Registered in **Unity Catalog** (BYO catalog) → the `enablement.salesforce` schema the
  dbt sources in `platform/models/staging/salesforce/_salesforce__sources.yml` read.

## Setup (UI)

1. **Create the destination - Managed Data Lake Service.**
   - Connectors → **Add destination** → *Managed Data Lake Service*.
   - Cloud storage: your S3 / ADLS / OneLake bucket.
   - Table format: **Delta and Iceberg** (dual).
   - Metadata catalog: **Databricks Unity Catalog** (bring-your-own). Provide the
     workspace URL, catalog name (`enablement`), and an OAuth/PAT credential with
     `CREATE SCHEMA`/`CREATE TABLE` on that catalog.
2. **Create the Salesforce connector.**
   - Add connector → **Salesforce** → authorize the org.
   - Destination schema: `salesforce` (matches `var('salesforce_schema')`).
   - Select objects: at minimum `Account`, `Contact`, `Opportunity`, `User`.
   - Sync frequency: e.g. every 15 min.
3. **Run the initial sync**, then confirm the tables in Unity Catalog:
   `enablement.salesforce.account`, `.opportunity`, etc.
4. **Point dbt at it** - the sources already resolve to
   `{{ var('source_catalog','enablement') }}.{{ var('salesforce_schema','salesforce') }}`.
   Then `dbt build --select staging.salesforce+ crm`.

## Representative config (Fivetran Terraform provider)

```hcl
resource "fivetran_destination" "mdls" {
  group_id           = fivetran_group.demo.id
  service            = "managed_data_lake"
  region             = "GCP_US_EAST4"   # match your storage region
  time_zone_offset   = "0"
  config {
    fivetran_role_arn = var.storage_role
    bucket            = var.lake_bucket
    table_format      = "DELTA_AND_ICEBERG"
    catalog           = "UNITY_CATALOG"
    catalog_name      = "enablement"
    databricks_host   = var.databricks_host
    # + Unity Catalog credential (OAuth/PAT) per Fivetran docs
  }
}

resource "fivetran_connector" "salesforce" {
  group_id  = fivetran_group.demo.id
  service   = "salesforce"
  config {
    schema = "salesforce"
  }
}
```

> Field names above are representative - confirm against the current Fivetran
> Terraform provider / UI. The durable design: MDLS lands dual-format open tables in
> Unity Catalog, and dbt reads them like any other UC source.
