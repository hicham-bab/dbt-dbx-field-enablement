-- Fusion-conformant: cast() only, no :: syntax
with customers as (
    select * from {{ ref('stg_customers') }}
),
customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),
final as (
    select
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.created_date,
        c.country,
        coalesce(co.number_of_orders,     0) as number_of_orders,
        coalesce(co.total_lifetime_value, cast(0 as decimal(18, 2))) as total_lifetime_value,
        co.first_order_date,
        co.most_recent_order_date,
        case
            when co.total_lifetime_value >= 500 then 'high_value'
            when co.total_lifetime_value >= 100 then 'mid_value'
            else 'low_value'
        end                                as customer_segment
    from customers c
    left join customer_orders co on c.customer_id = co.customer_id
)
select * from final
