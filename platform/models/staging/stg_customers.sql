with source as (
    select * from {{ source('ecommerce_raw', 'raw_customers') }}
),
renamed as (
    select
        customer_id,
        first_name,
        last_name,
        lower(email)             as email,
        cast(created_at as date) as created_date,
        upper(country)           as country
    from source
)
select * from renamed
