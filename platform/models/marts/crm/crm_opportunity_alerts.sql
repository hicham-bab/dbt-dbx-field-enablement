-- Governed activation feed: the exact rows Fivetran Activations pushes to Slack.
-- Because it's a dbt model on top of the contracted fct_opportunities mart, the
-- alert logic is version-controlled, tested, and lineage-tracked — the same
-- governed definition Genie uses. See fivetran/activations_slack.md.

with opportunities as (
    select * from {{ ref('fct_opportunities') }}
),
flagged as (
    select
        opportunity_id,
        account_id,
        account_name,
        opportunity_name,
        opportunity_owner,
        stage_name,
        amount,
        close_date,
        case
            when amount >= cast(100000 as decimal(18, 2)) then 'high_value_open'
            else 'overdue_open'
        end as alert_reason
    from opportunities
    where not is_closed
      and (amount >= cast(100000 as decimal(18, 2)) or close_date < current_date())
)
select * from flagged
