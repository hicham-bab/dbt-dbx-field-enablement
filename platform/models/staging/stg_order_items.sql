with source as (
    select * from {{ source('ecommerce_raw', 'raw_order_items') }}
),
renamed as (
    select
        order_item_id,
        order_id,
        product_id,
        quantity,
        unit_price,
        quantity * unit_price as line_total
    from source
)
select * from renamed
