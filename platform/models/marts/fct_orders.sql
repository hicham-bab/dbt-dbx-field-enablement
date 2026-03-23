-- Fusion-conformant: cast() only, no :: syntax
with orders as (
    select * from {{ ref('stg_orders') }}
),
order_items_enriched as (
    select
        order_id,
        count(order_item_id)             as number_of_items,
        sum(line_total)                  as items_total
    from {{ ref('int_order_items_enriched') }}
    group by order_id
),
payments as (
    select
        order_id,
        sum(case when payment_status = 'success' then amount else 0 end) as amount_paid
    from {{ ref('stg_payments') }}
    group by order_id
),
final as (
    select
        o.order_id,
        o.customer_id,
        o.order_date,
        o.status,
        o.payment_method,
        coalesce(oi.number_of_items, 0)               as number_of_items,
        coalesce(oi.items_total,     cast(0 as decimal(18, 2))) as items_total,
        coalesce(p.amount_paid,      cast(0 as decimal(18, 2))) as amount_paid
    from orders o
    left join order_items_enriched oi on o.order_id = oi.order_id
    left join payments p on o.order_id = p.order_id
)
select * from final
