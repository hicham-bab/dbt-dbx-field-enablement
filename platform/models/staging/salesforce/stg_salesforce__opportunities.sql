with source as (
    select * from {{ source('salesforce', 'opportunity') }}
),
renamed as (
    select
        id                              as opportunity_id,
        account_id,
        name                           as opportunity_name,
        stage_name,
        cast(amount as decimal(18, 2)) as amount,
        cast(close_date as date)       as close_date,
        cast(probability as decimal(5, 2)) as probability,
        coalesce(is_closed, false)     as is_closed,
        coalesce(is_won, false)        as is_won,
        type                           as opportunity_type,
        lead_source,
        owner_id,
        cast(created_date as date)     as created_date
    from source
    where not coalesce(_fivetran_deleted, false)
)
select * from renamed
