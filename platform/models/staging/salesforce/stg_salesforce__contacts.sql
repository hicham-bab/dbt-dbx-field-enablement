with source as (
    select * from {{ source('salesforce', 'contact') }}
),
renamed as (
    select
        id                          as contact_id,
        account_id,
        first_name,
        last_name,
        lower(email)               as email,
        title,
        owner_id,
        cast(created_date as date) as created_date
    from source
    where not coalesce(_fivetran_deleted, false)
)
select * from renamed
