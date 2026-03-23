with orders as (
    select * from {{ ref('stg_orders') }}
),
payments as (
    select * from {{ ref('stg_payments') }}
),
order_payments as (
    select
        order_id,
        sum(case when payment_status = 'success' then amount else 0 end) as amount_paid,
        max(payment_date)                                                  as latest_payment_date
    from payments
    group by order_id
),
customer_orders as (
    select
        o.customer_id,
        count(o.order_id)          as number_of_orders,
        sum(op.amount_paid)        as total_lifetime_value,
        min(o.order_date)          as first_order_date,
        max(o.order_date)          as most_recent_order_date
    from orders o
    left join order_payments op on o.order_id = op.order_id
    group by o.customer_id
)
select * from customer_orders
