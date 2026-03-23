-- Fusion-conformant: cast() only, date functions use standard SQL syntax
-- Cross-project refs from platform project

with customers as (
    select * from {{ ref('platform', 'dim_customers') }}
),

orders as (
    select * from {{ ref('platform', 'fct_orders') }}
),

customer_recency as (
    select
        customer_id,
        max(order_date)                                                  as last_order_date,
        count(distinct case when status = 'completed' then order_id end) as completed_orders,
        datediff(current_date(), max(order_date))                        as days_since_last_order
    from orders
    group by customer_id
),

final as (
    select
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.country,
        c.customer_segment,
        c.total_lifetime_value,
        c.number_of_orders,
        cr.last_order_date,
        cr.completed_orders,
        cr.days_since_last_order,

        case
            when cr.days_since_last_order <= 30  and c.customer_segment = 'high_value'               then 'champion'
            when cr.days_since_last_order <= 90  and c.customer_segment in ('high_value', 'mid_value') then 'loyal'
            when cr.days_since_last_order <= 180                                                       then 'at_risk'
            when cr.days_since_last_order >  180                                                       then 'lapsed'
            when cr.last_order_date is null                                                             then 'never_purchased'
            else 'other'
        end                                                              as marketing_segment
    from customers c
    left join customer_recency cr on c.customer_id = cr.customer_id
)

select * from final
