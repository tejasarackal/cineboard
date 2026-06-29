with movie_budget as (
    select
        movie_id,
        budget,
        revenue,
        profit,
        vote_average
    from {{ ref('fact_movie') }}
    where has_financial_data = true
)
select
    {{ budget_tier(budget) }} as budget_tier,
    count(*) as movie_count,
    sum(coalesce(revenue, 0)) as total_revenue,
    round(avg(revenue), 2) as average_revenue,
    round(avg(profit), 2) as average_profit,
    round(avg(vote_average), 2) as average_rating
from movie_budget
group by budget_tier
order by budget_tier