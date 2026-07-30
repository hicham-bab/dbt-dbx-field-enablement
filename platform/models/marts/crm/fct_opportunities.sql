with opportunities as (
    select * from {{ ref('stg_salesforce__opportunities') }}
),
accounts as (
    select * from {{ ref('stg_salesforce__accounts') }}
),
users as (
    select * from {{ ref('stg_salesforce__users') }}
),
final as (
    select
        o.opportunity_id,
        o.account_id,
        a.account_name,
        o.opportunity_name,
        o.stage_name,
        o.amount,
        o.close_date,
        o.probability,
        o.is_closed,
        o.is_won,
        o.opportunity_type,
        o.lead_source,
        o.owner_id,
        u.user_name as opportunity_owner,
        cast(o.amount * o.probability / 100 as decimal(18, 2)) as weighted_amount,
        o.created_date
    from opportunities o
    left join accounts a on o.account_id = a.account_id
    left join users u on o.owner_id = u.user_id
)
select * from final
