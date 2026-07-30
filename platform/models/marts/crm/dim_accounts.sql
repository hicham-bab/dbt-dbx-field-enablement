with accounts as (
    select * from {{ ref('stg_salesforce__accounts') }}
),
users as (
    select * from {{ ref('stg_salesforce__users') }}
),
final as (
    select
        a.account_id,
        a.account_name,
        a.account_type,
        a.industry,
        a.annual_revenue,
        a.number_of_employees,
        a.billing_country,
        a.owner_id,
        u.user_name as account_owner,
        a.created_date
    from accounts a
    left join users u on a.owner_id = u.user_id
)
select * from final
