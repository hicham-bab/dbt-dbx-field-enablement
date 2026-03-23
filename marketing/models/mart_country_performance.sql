-- Fusion-conformant: cast() only, no :: syntax
-- Cross-project refs from platform project

with customers as (
    select * from {{ ref('platform', 'dim_customers') }}
),

orders as (
    select * from {{ ref('platform', 'fct_orders') }}
),

final as (
    select
        c.country,
        count(distinct c.customer_id)                                        as total_customers,
        count(distinct case
            when c.customer_segment = 'high_value' then c.customer_id
        end)                                                                 as high_value_customers,
        count(distinct o.order_id)                                           as total_orders,
        sum(case when o.status = 'completed' then o.amount_paid else 0 end)  as recognised_revenue,
        avg(c.total_lifetime_value)                                          as avg_ltv,
        sum(case when o.status = 'completed' then o.amount_paid else 0 end)
            / nullif(cast(count(distinct c.customer_id) as decimal(18, 2)), 0) as revenue_per_customer
    from customers c
    left join orders o on c.customer_id = o.customer_id
    group by c.country
)

select * from final
