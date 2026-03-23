with source as (
    select * from {{ source('ecommerce_raw', 'raw_orders') }}
),
renamed as (
    select
        order_id,
        customer_id,
        cast(order_date as date)      as order_date,
        lower(status)                 as status,
        amount,
        lower(payment_method)         as payment_method
    from source
)
select * from renamed
