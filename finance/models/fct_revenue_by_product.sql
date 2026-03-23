-- Fusion-conformant: cast() only, no :: syntax
-- Cross-project refs from platform project — demonstrates multi-table Mesh refs

with orders as (
    select * from {{ ref('platform', 'fct_orders') }}
),

products as (
    select * from {{ ref('platform', 'dim_products') }}
),

-- We need order items to link orders to products.
-- Since order items are in the platform staging layer (protected),
-- we join at the fct_orders grain using the product dimension.
-- This model shows revenue attribution at the product level using fct_orders.

order_product_revenue as (
    select
        o.order_id,
        o.status,
        o.amount_paid,
        -- We attribute full order revenue to each product in the order for simplicity.
        -- In production, join to stg_order_items for line-level attribution.
        o.order_date
    from orders o
),

-- Aggregate to product level using dim_products as the spine
product_summary as (
    select
        p.product_id,
        p.product_name,
        p.category,
        p.unit_price,
        p.is_active,
        count(distinct opr.order_id)                                         as total_orders,
        sum(case when opr.status = 'completed' then opr.amount_paid else cast(0 as decimal(18,2)) end)
                                                                             as recognised_revenue,
        count(distinct case when opr.status = 'returned' then opr.order_id end)
                                                                             as return_count,
        min(opr.order_date)                                                  as first_order_date,
        max(opr.order_date)                                                  as most_recent_order_date
    from products p
    left join order_product_revenue opr on 1 = 1  -- cross-join for demo; replace with line-item join in prod
    group by p.product_id, p.product_name, p.category, p.unit_price, p.is_active
)

select * from product_summary
