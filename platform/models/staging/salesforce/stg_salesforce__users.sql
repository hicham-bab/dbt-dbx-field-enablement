with source as (
    select * from {{ source('salesforce', 'user') }}
),
renamed as (
    select
        id                       as user_id,
        name                     as user_name,
        lower(email)             as email,
        coalesce(is_active, false) as is_active
    from source
    where not coalesce(_fivetran_deleted, false)
)
select * from renamed
