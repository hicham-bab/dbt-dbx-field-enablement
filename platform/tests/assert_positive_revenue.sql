-- Custom singular test: no completed orders should have amount_paid <= 0
-- This demonstrates dbt's ability to encode business rules as testable SQL
-- that lives next to the model and is reviewed in the same PR.

select
    order_id,
    status,
    amount_paid
from {{ ref('fct_orders') }}
where status = 'completed'
  and amount_paid <= 0
