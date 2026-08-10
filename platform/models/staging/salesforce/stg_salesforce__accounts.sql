with source as (
    select * from {{ source('salesforce', 'account') }}
),
renamed as (
    select
        id                              as account_id,
        name                           as account_name,
        type                           as account_type,
        industry,
        cast(annual_revenue as decimal(18, 2)) as annual_revenue,
        cast(number_of_employees as bigint)    as number_of_employees,
        upper(billing_country)         as billing_country,
        owner_id,
        cast(created_date as date)     as created_date
    from source
    where not coalesce(_fivetran_deleted, false)
)
select * from renamed
