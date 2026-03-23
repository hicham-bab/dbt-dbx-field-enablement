with products as (
    select * from {{ ref('stg_products') }}
)
select
    product_id,
    product_name,
    category,
    unit_price,
    is_active
from products
