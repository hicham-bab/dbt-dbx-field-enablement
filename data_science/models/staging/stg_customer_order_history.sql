-- Fusion-conformant: cast() only, no :: syntax
-- Cross-project refs from platform project
-- Prepares a customer-order grain for downstream Python feature models

with customers as (
    select * from {{ ref('platform', 'dim_customers') }}
),

orders as (
    select * from {{ ref('platform', 'fct_orders') }}
),

final as (
    select
        c.customer_id,
        c.customer_segment,
        c.country,
        c.total_lifetime_value,
        c.number_of_orders,
        c.first_order_date,
        c.most_recent_order_date,
        o.order_id,
        o.order_date,
        o.status,
        o.payment_method,
        o.number_of_items,
        o.items_total,
        o.amount_paid,
        datediff(current_date(), c.most_recent_order_date) as days_since_last_order,
        datediff(c.most_recent_order_date, c.first_order_date) as customer_tenure_days
    from customers c
    inner join orders o on c.customer_id = o.customer_id
)

select * from final
