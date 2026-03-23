-- Fusion-conformant: cast() only, no :: syntax
with source as (
    select * from {{ source('ecommerce_raw', 'raw_products') }}
),
renamed as (
    select
        product_id,
        product_name,
        lower(category)              as category,
        unit_price,
        cast(is_active as boolean)   as is_active
    from source
)
select * from renamed
