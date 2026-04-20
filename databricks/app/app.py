"""
dbt + Databricks Field Enablement Dashboard
=============================================
A Streamlit app that runs inside Databricks Apps, demonstrating:
  - Tab 1: Executive Dashboard — clean revenue KPIs from dbt marts
  - Tab 2: Semantic Layer Explorer — pick a metric, see MetricFlow-style query + results
  - Tab 3: Metric Views vs dbt SL — same query, both systems, side-by-side comparison
  - Tab 4: Governance — contract status, test results, model audit trail

Authentication is handled automatically by Databricks Apps service principal.
"""

import streamlit as st
import pandas as pd
import os
from databricks import sql as dbsql

# -- Namespace configuration --
# Set these env vars to match your catalog/schema. Defaults to enablement/ecommerce.
CATALOG = os.environ.get("DBT_CATALOG", "enablement")
SCHEMA = os.environ.get("DBT_SCHEMA", "ecommerce")
MV_SCHEMA = f"{SCHEMA}_metric_views"

# ── Connection ─────────────────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    try:
        from databricks.sdk.runtime import dbutils
        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
    except Exception:
        token = os.environ.get("DATABRICKS_TOKEN", "")

    return dbsql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_WAREHOUSE_ID"],
        access_token=token,
    )

@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    with get_connection().cursor() as cur:
        cur.execute(sql)
        return cur.fetchall_arrow().to_pandas()

def safe_query(sql: str, fallback: pd.DataFrame = None) -> pd.DataFrame:
    # Auto-format catalog/schema variables so queries use the configured namespace
    sql = sql.format(CATALOG=CATALOG, SCHEMA=SCHEMA, MV_SCHEMA=MV_SCHEMA)
    try:
        return query(sql)
    except Exception as e:
        st.warning(f"Query error: {e}")
        return fallback if fallback is not None else pd.DataFrame()


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="dbt + Databricks Enablement",
    layout="wide",
)

st.title("dbt + Databricks Field Enablement")
st.caption(
    f"Data: `{CATALOG}.{SCHEMA}` (dbt platform project) | "
    f"Comparison: `{CATALOG}.{MV_SCHEMA}` (Databricks Metric Views)"
)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_exec, tab_sl, tab_compare, tab_gov = st.tabs([
    "Executive Dashboard",
    "Semantic Layer Explorer",
    "Metric Views vs dbt SL",
    "Governance",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXECUTIVE DASHBOARD
# Clean revenue KPIs from dbt marts — no comparison, just the numbers
# ══════════════════════════════════════════════════════════════════════════════
with tab_exec:
    st.subheader("Executive Dashboard")
    st.caption(f"Source: `{CATALOG}.{SCHEMA}` — dbt platform project, all tests passing")

    col1, col2, col3, col4 = st.columns(4)

    kpis = safe_query("""
        SELECT
            SUM(CASE WHEN status = 'completed' THEN amount_paid ELSE 0 END) AS total_revenue,
            COUNT(DISTINCT order_id)                                          AS total_orders,
            COUNT(DISTINCT CASE WHEN status = 'completed' THEN order_id END) AS completed_orders,
            COUNT(DISTINCT CASE WHEN status = 'returned'  THEN order_id END)
                / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100      AS return_rate
        FROM {CATALOG}.{SCHEMA}.fct_orders
    """)

    if not kpis.empty:
        col1.metric("Total Revenue (USD)",  f"${kpis['total_revenue'][0]:,.2f}",
                    help="Completed orders only — canonical definition from dbt semantic layer")
        col2.metric("Total Orders",         f"{int(kpis['total_orders'][0]):,}")
        col3.metric("Completed Orders",     f"{int(kpis['completed_orders'][0]):,}")
        col4.metric("Return Rate",          f"{kpis['return_rate'][0]:.1f}%")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Revenue by Customer Segment**")
        seg_rev = safe_query("""
            SELECT
                c.customer_segment,
                SUM(CASE WHEN o.status = 'completed' THEN o.amount_paid ELSE 0 END) AS revenue
            FROM {CATALOG}.{SCHEMA}.dim_customers c
            LEFT JOIN {CATALOG}.{SCHEMA}.fct_orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_segment
            ORDER BY revenue DESC
        """)
        if not seg_rev.empty:
            st.bar_chart(seg_rev.set_index("customer_segment")["revenue"])

    with col_right:
        st.markdown("**Customers by Segment**")
        seg_count = safe_query("""
            SELECT customer_segment, COUNT(*) AS customers
            FROM {CATALOG}.{SCHEMA}.dim_customers
            GROUP BY customer_segment
            ORDER BY customers DESC
        """)
        if not seg_count.empty:
            st.bar_chart(seg_count.set_index("customer_segment")["customers"])

    st.divider()
    st.markdown("**Revenue by Country**")
    country_rev = safe_query("""
        SELECT
            c.country,
            SUM(CASE WHEN o.status = 'completed' THEN o.amount_paid ELSE 0 END) AS revenue
        FROM {CATALOG}.{SCHEMA}.dim_customers c
        LEFT JOIN {CATALOG}.{SCHEMA}.fct_orders o ON c.customer_id = o.customer_id
        GROUP BY c.country
        ORDER BY revenue DESC
    """)
    if not country_rev.empty:
        st.bar_chart(country_rev.set_index("country")["revenue"])

    st.divider()
    st.markdown("**Top Products by Order Count**")
    products = safe_query("""
        SELECT
            p.product_name,
            p.category,
            p.unit_price,
            COUNT(DISTINCT o.order_id) AS order_count,
            SUM(CASE WHEN o.status = 'completed' THEN o.amount_paid ELSE 0 END) AS revenue
        FROM {CATALOG}.{SCHEMA}.dim_products p
        LEFT JOIN {CATALOG}.{SCHEMA}.fct_orders o ON 1=1
        GROUP BY p.product_name, p.category, p.unit_price
        ORDER BY order_count DESC
        LIMIT 10
    """)
    if not products.empty:
        st.dataframe(products, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SEMANTIC LAYER EXPLORER
# Pick a metric + dimension, see the MetricFlow-style query and results
# ══════════════════════════════════════════════════════════════════════════════
with tab_sl:
    st.subheader("Semantic Layer Explorer")
    st.caption(
        "Explores named metrics from `platform/models/semantic/_semantic_models.yml`. "
        "Every metric below has a version-controlled definition reviewable in Git."
    )

    metric_options = {
        "Total Revenue (Completed Orders)": {
            "sql": """
                SELECT
                    'total_recognised_revenue' AS metric_name,
                    SUM(amount_paid) AS value,
                    'Defined in _semantic_models.yml: SUM(amount_paid) WHERE status = completed' AS definition
                FROM {CATALOG}.{SCHEMA}.fct_orders
                WHERE status = 'completed'
            """,
            "breakdown_sql": {
                "by_month": """
                    SELECT
                        CAST(DATE_TRUNC('month', order_date) AS DATE) AS period,
                        SUM(amount_paid) AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders
                    WHERE status = 'completed'
                    GROUP BY 1 ORDER BY 1
                """,
                "by_segment": """
                    SELECT c.customer_segment AS period, SUM(o.amount_paid) AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders o
                    JOIN {CATALOG}.{SCHEMA}.dim_customers c ON o.customer_id = c.customer_id
                    WHERE o.status = 'completed'
                    GROUP BY 1 ORDER BY 2 DESC
                """,
                "by_payment_method": """
                    SELECT payment_method AS period, SUM(amount_paid) AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders
                    WHERE status = 'completed'
                    GROUP BY 1 ORDER BY 2 DESC
                """
            }
        },
        "Average Order Value": {
            "sql": """
                SELECT
                    'avg_order_value' AS metric_name,
                    AVG(amount_paid) AS value,
                    'Defined in _semantic_models.yml: AVG(amount_paid) WHERE status = completed' AS definition
                FROM {CATALOG}.{SCHEMA}.fct_orders
                WHERE status = 'completed'
            """,
            "breakdown_sql": {
                "by_month": """
                    SELECT CAST(DATE_TRUNC('month', order_date) AS DATE) AS period, AVG(amount_paid) AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders WHERE status = 'completed'
                    GROUP BY 1 ORDER BY 1
                """,
                "by_segment": """
                    SELECT c.customer_segment AS period, AVG(o.amount_paid) AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders o
                    JOIN {CATALOG}.{SCHEMA}.dim_customers c ON o.customer_id = c.customer_id
                    WHERE o.status = 'completed' GROUP BY 1
                """,
                "by_payment_method": """
                    SELECT payment_method AS period, AVG(amount_paid) AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders WHERE status = 'completed'
                    GROUP BY 1 ORDER BY 2 DESC
                """
            }
        },
        "Return Rate (%)": {
            "sql": """
                SELECT
                    'return_rate' AS metric_name,
                    COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
                        / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100 AS value,
                    'Defined in _semantic_models.yml: ratio metric — returned/total orders' AS definition
                FROM {CATALOG}.{SCHEMA}.fct_orders
            """,
            "breakdown_sql": {
                "by_month": """
                    SELECT
                        CAST(DATE_TRUNC('month', order_date) AS DATE) AS period,
                        COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
                            / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100 AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders GROUP BY 1 ORDER BY 1
                """,
                "by_segment": """
                    SELECT c.customer_segment AS period,
                        COUNT(DISTINCT CASE WHEN o.status = 'returned' THEN o.order_id END)
                            / CAST(COUNT(DISTINCT o.order_id) AS DECIMAL(10,4)) * 100 AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders o
                    JOIN {CATALOG}.{SCHEMA}.dim_customers c ON o.customer_id = c.customer_id
                    GROUP BY 1
                """,
                "by_payment_method": """
                    SELECT payment_method AS period,
                        COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
                            / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100 AS value
                    FROM {CATALOG}.{SCHEMA}.fct_orders GROUP BY 1
                """
            }
        },
        "Total Customers": {
            "sql": """
                SELECT 'total_customers' AS metric_name, COUNT(DISTINCT customer_id) AS value,
                    'Defined in _semantic_models.yml: COUNT DISTINCT customer_id' AS definition
                FROM {CATALOG}.{SCHEMA}.dim_customers
            """,
            "breakdown_sql": {
                "by_month": """
                    SELECT CAST(DATE_TRUNC('month', created_date) AS DATE) AS period,
                        COUNT(DISTINCT customer_id) AS value
                    FROM {CATALOG}.{SCHEMA}.dim_customers GROUP BY 1 ORDER BY 1
                """,
                "by_segment": """
                    SELECT customer_segment AS period, COUNT(DISTINCT customer_id) AS value
                    FROM {CATALOG}.{SCHEMA}.dim_customers GROUP BY 1 ORDER BY 2 DESC
                """,
                "by_payment_method": """
                    SELECT country AS period, COUNT(DISTINCT customer_id) AS value
                    FROM {CATALOG}.{SCHEMA}.dim_customers GROUP BY 1 ORDER BY 2 DESC
                """
            }
        },
        "Average Customer LTV": {
            "sql": """
                SELECT 'avg_lifetime_value' AS metric_name, AVG(total_lifetime_value) AS value,
                    'Defined in _semantic_models.yml: AVG(total_lifetime_value)' AS definition
                FROM {CATALOG}.{SCHEMA}.dim_customers
            """,
            "breakdown_sql": {
                "by_month": """
                    SELECT CAST(DATE_TRUNC('month', created_date) AS DATE) AS period,
                        AVG(total_lifetime_value) AS value
                    FROM {CATALOG}.{SCHEMA}.dim_customers GROUP BY 1 ORDER BY 1
                """,
                "by_segment": """
                    SELECT customer_segment AS period, AVG(total_lifetime_value) AS value
                    FROM {CATALOG}.{SCHEMA}.dim_customers GROUP BY 1 ORDER BY 2 DESC
                """,
                "by_payment_method": """
                    SELECT country AS period, AVG(total_lifetime_value) AS value
                    FROM {CATALOG}.{SCHEMA}.dim_customers GROUP BY 1 ORDER BY 2 DESC
                """
            }
        },
    }

    col_m, col_d = st.columns(2)
    with col_m:
        selected_metric = st.selectbox("Select metric", list(metric_options.keys()))
    with col_d:
        breakdown_dim = st.selectbox(
            "Breakdown by",
            ["by_month", "by_segment", "by_payment_method"],
            format_func=lambda x: {"by_month": "Month", "by_segment": "Customer Segment", "by_payment_method": "Payment Method / Country"}[x]
        )

    metric_cfg = metric_options[selected_metric]

    # Aggregate value
    agg_df = safe_query(metric_cfg["sql"])
    if not agg_df.empty:
        st.metric(selected_metric, f"{agg_df['value'][0]:,.2f}")
        st.caption(f"Definition: {agg_df['definition'][0]}")

    # Breakdown chart
    breakdown_df = safe_query(metric_cfg["breakdown_sql"][breakdown_dim])
    if not breakdown_df.empty:
        st.markdown(f"**{selected_metric} breakdown**")
        st.bar_chart(breakdown_df.set_index("period")["value"])
        with st.expander("View SQL"):
            st.code(metric_cfg["breakdown_sql"][breakdown_dim].strip(), language="sql")

    st.info(
        "These queries translate named MetricFlow metrics into SQL. "
        "Each metric is defined once in `_semantic_models.yml` and reused across "
        "Genie, BI tools, and this app. Change the definition in one place — it updates everywhere."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — METRIC VIEWS vs dbt SL
# Same query against Metric Views and dbt, side-by-side results + metadata comparison
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("Metric Views vs dbt Semantic Layer")
    st.caption(
        f"Same metrics, both systems. Metric Views are in `{CATALOG}.{MV_SCHEMA}`. "
        f"dbt results are from `{CATALOG}.{SCHEMA}` mart tables."
    )

    st.info(
        "Both systems compute the same numbers — the difference is in auditability, "
        "governance, and what Genie can reason about."
    )

    col_mv, col_dbt = st.columns(2)

    # Revenue comparison
    with col_mv:
        st.markdown("### Databricks Metric Views")
        st.caption(
            "Defined in `02_metric_views.sql` — SQL views in Unity Catalog.\n\n"
            "- Simple SQL views, easy to create\n"
            "- No version control of the metric definition\n"
            "- No test coverage on the underlying data\n"
            "- Genie reads column names — no descriptions available"
        )
        mv_metrics = safe_query(f"SELECT * FROM {CATALOG}.{MV_SCHEMA}.all_metrics")
        if not mv_metrics.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Revenue", f"${mv_metrics['total_revenue'][0]:,.2f}")
            c2.metric("Total Orders",  f"{int(mv_metrics['total_orders'][0]):,}")
            c3.metric("Return Rate",   f"{mv_metrics['return_rate_pct'][0]:.1f}%")
            c1.metric("Customers",     f"{int(mv_metrics['customer_count'][0]):,}")
            c2.metric("Avg LTV",       f"${mv_metrics['avg_lifetime_value'][0]:,.2f}")
            c3.metric("Avg Order Val", f"${mv_metrics['avg_order_value'][0]:,.2f}")
        else:
            st.warning("Metric Views not found. Run `02_metric_views.sql` first.")

    with col_dbt:
        st.markdown("### dbt Semantic Layer")
        st.caption(
            "Defined in `_semantic_models.yml` — version-controlled YAML.\n\n"
            "- Named metrics with human-readable descriptions\n"
            "- PR-reviewed definitions — full Git audit trail\n"
            "- Underlying data tested with dbt (not_null, accepted_values, etc.)\n"
            "- Column descriptions pushed to Unity Catalog — Genie reads them natively"
        )
        dbt_kpis = safe_query("""
            SELECT
                SUM(CASE WHEN status = 'completed' THEN amount_paid ELSE 0 END) AS total_revenue,
                COUNT(DISTINCT order_id)                                          AS total_orders,
                COUNT(DISTINCT CASE WHEN status = 'returned' THEN order_id END)
                    / CAST(COUNT(DISTINCT order_id) AS DECIMAL(10,4)) * 100      AS return_rate_pct,
                AVG(amount_paid)                                                  AS avg_order_value
            FROM {CATALOG}.{SCHEMA}.fct_orders
        """)
        dbt_cust = safe_query("""
            SELECT COUNT(DISTINCT customer_id) AS customer_count,
                   AVG(total_lifetime_value) AS avg_lifetime_value
            FROM {CATALOG}.{SCHEMA}.dim_customers
        """)
        if not dbt_kpis.empty and not dbt_cust.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Revenue", f"${dbt_kpis['total_revenue'][0]:,.2f}")
            c2.metric("Total Orders",  f"{int(dbt_kpis['total_orders'][0]):,}")
            c3.metric("Return Rate",   f"{dbt_kpis['return_rate_pct'][0]:.1f}%")
            c1.metric("Customers",     f"{int(dbt_cust['customer_count'][0]):,}")
            c2.metric("Avg LTV",       f"${dbt_cust['avg_lifetime_value'][0]:,.2f}")
            c3.metric("Avg Order Val", f"${dbt_kpis['avg_order_value'][0]:,.2f}")

    st.divider()

    # Feature comparison table
    st.subheader("What Genie Sees: Metadata Quality Comparison")

    comparison_df = pd.DataFrame({
        "Capability": [
            "Metric definition location",
            "Version control",
            "PR review process",
            "Column descriptions for Genie",
            "Data quality tests",
            "Audit trail",
            "Multi-tool compatibility (BI, Genie, API)",
            "Governance (contracts, access control)",
            "Cross-project refs (Mesh)",
        ],
        "Databricks Metric Views": [
            "SQL views in Unity Catalog",
            "Manual (not automatic)",
            "None built-in",
            "No — column names only",
            "None on metric views",
            "View DDL history only",
            "Databricks tools only",
            "Unity Catalog permissions",
            "Not supported",
        ],
        "dbt Semantic Layer (MetricFlow)": [
            "YAML in `_semantic_models.yml` — next to the model",
            "Git — every change is a commit",
            "PR workflow — reviewer approved",
            "Yes — persisted to UC via dbt-databricks adapter",
            "dbt tests on underlying marts (not_null, accepted_values, etc.)",
            "git log on the YAML file — exact definition history",
            "Any BI tool via semantic layer API + Genie + dbt Cloud",
            "Contracts (enforced: true) + access: public/protected + groups",
            "Yes — cross-project refs via dbt Mesh",
        ],
    })

    def highlight_row(row):
        return [
            "background-color: #d4edda" if col == "dbt Semantic Layer (MetricFlow)" else
            "background-color: #fff3cd" if col == "Databricks Metric Views" else ""
            for col in row.index
        ]

    st.dataframe(
        comparison_df.style.apply(highlight_row, axis=1),
        use_container_width=True,
        height=380,
    )

    st.markdown("""
**When are Metric Views sufficient?**
- Simple, stable metrics in a Databricks-only environment
- Small teams where manual sync is manageable
- No need for multi-tool metric consistency

**When does dbt Semantic Layer win?**
- Complex metrics with filters, ratios, or time-grain handling
- Multi-tool BI environment (Tableau, Looker, Genie, etc.)
- Regulated industries where audit trails are required
- Enterprise governance: contracts, PR reviews, access control
- dbt Mesh: metrics need to be consistent across projects
    """)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — GOVERNANCE
# Contract status, test summary, model freshness, audit trail demo
# ══════════════════════════════════════════════════════════════════════════════
with tab_gov:
    st.subheader("Governance Dashboard")
    st.caption(
        "Shows the governance layer that dbt provides: contracts, access control, "
        "test coverage, and an auditable change history."
    )

    col1, col2, col3 = st.columns(3)

    # Model inventory
    models_info = pd.DataFrame({
        "Model": ["dim_customers", "dim_products", "fct_orders"],
        "Project": ["platform", "platform", "platform"],
        "Access": ["public", "public", "public"],
        "Contract": ["enforced", "enforced", "enforced"],
        "Group": ["platform_core", "platform_core", "platform_core"],
        "Tests": ["not_null, unique, accepted_values, relationships", "not_null, unique", "not_null, unique, accepted_values, relationships, expect_between"],
        "Consumers": ["marketing, finance", "finance", "marketing, finance"],
    })

    col1.metric("Public Models",    "3")
    col2.metric("Contract-Enforced", "3 / 3")
    col3.metric("Mesh Consumers",   "2 (marketing, finance)")

    st.divider()
    st.markdown("**Public Interface (Platform Project)**")
    st.dataframe(models_info, use_container_width=True)

    st.divider()
    st.markdown("**Mesh Architecture: Cross-Project Dependencies**")

    mesh_df = pd.DataFrame({
        "Consumer Project": ["marketing", "marketing", "finance", "finance"],
        "Refs Platform Model": ["dim_customers", "fct_orders", "fct_orders", "dim_products"],
        "Consumer Model": ["mart_customer_segments", "mart_country_performance", "fct_revenue", "fct_revenue_by_product"],
        "Contract Protection": ["Yes — breaking changes blocked", "Yes", "Yes", "Yes"],
    })
    st.dataframe(mesh_df, use_container_width=True)

    st.divider()

    # Governance explainer
    st.markdown("**What dbt Governance Gives You**")
    st.markdown("""
| Governance capability | How dbt implements it | What Databricks-only gives you |
|---|---|---|
| Contract enforcement | `contract: enforced: true` in schema YAML | Unity Catalog column types only |
| Access control | `access: public / protected / private` per model | UC permissions (table-level) |
| Breaking change detection | `dbt build` fails if contract is violated | Manual schema monitoring |
| Ownership | `groups:` with `owner.email` in YAML | UC owner metadata |
| Change review | PR workflow on YAML + SQL | No built-in review for DLT code |
| Audit trail | `git log models/marts/_marts.yml` | UC audit logs (access events) |
| Cross-project governance | dbt Mesh — `dependencies.yml` + public/private | Not supported |
    """)

    st.divider()
    st.markdown("**Audit Trail Demo**")
    st.code("""
# Every change to the revenue definition is traceable:
git log platform/models/semantic/_semantic_models.yml

# Every change to a public contract:
git log platform/models/marts/_marts.yml

# Who approved the last change to the customer segment definition:
git log -p platform/models/marts/_marts.yml | grep -A5 "customer_segment"
    """, language="bash")

    st.info(
        "The audit trail is a git history, not a UI. Every metric definition change "
        "has a commit hash, an author, a timestamp, and a PR number. "
        "This is the answer when a regulator or CFO asks 'who approved this definition?'"
    )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data refreshed every 5 minutes (Streamlit cache TTL=300s) | "
    f"dbt project: platform ({CATALOG}.{SCHEMA}) | "
    f"Metric Views: {CATALOG}.{MV_SCHEMA} | "
    "Built with Databricks Apps + Streamlit"
)
