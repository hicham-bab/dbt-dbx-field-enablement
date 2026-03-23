-- Fusion-conformant: cast() only, no :: syntax
-- Cross-project ref from platform project

with orders as (
    select * from {{ ref('platform', 'fct_orders') }}
),

final as (
    select
        order_id,
        customer_id,
        order_date,
        cast(date_trunc('month', order_date) as date)   as order_month,
        cast(date_trunc('year',  order_date) as date)   as order_year,
        status,
        payment_method,
        number_of_items,
        items_total,
        amount_paid,

        case
            when status = 'completed' then amount_paid
            else cast(0 as decimal(18, 2))
        end                                             as recognised_revenue,

        case
            when status = 'returned' then amount_paid
            else cast(0 as decimal(18, 2))
        end                                             as returned_amount
    from orders
)

select * from final
