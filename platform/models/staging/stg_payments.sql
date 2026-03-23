with source as (
    select * from {{ source('ecommerce_raw', 'raw_payments') }}
),
renamed as (
    select
        payment_id,
        order_id,
        lower(payment_method)         as payment_method,
        amount,
        lower(status)                 as payment_status,
        cast(payment_date as date)    as payment_date
    from source
)
select * from renamed
