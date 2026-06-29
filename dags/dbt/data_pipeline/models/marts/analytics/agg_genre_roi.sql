with movie_releases as (
    select
        movie_id,
        release_date,
        extract(year from release_date)::int as release_year,
        extract(month from release_date)::int as release_month,
        case when has_financial_data then revenue_to_budget_ratio else null end as revenue_to_budget_ratio,
        case when has_financial_data then profit_margin else null end as profit_margin
    from {{ ref('fact_movie') }}
    where release_date is not null 
),
movie_genre as (
    select
        m.movie_id as movie_id,
        d.genre_name as genre_name,
        m.release_year as release_year,
        m.release_month as release_month,
        m.revenue_to_budget_ratio as revenue_to_budget_ratio,
        m.profit_margin as profit_margin
    from {{ ref('bridge_movie_genre') }} as b
    inner join {{ ref('dim_genre') }} as d on b.genre_id = d.genre_id
    inner join movie_releases as m on b.movie_id = m.movie_id
)
select
    genre_name,
    release_year,
    count(*) as movie_count,
    count(revenue_to_budget_ratio) as movie_count_with_financial_data,
    round(avg(revenue_to_budget_ratio), 2) as average_revenue_to_budget_ratio,
    round(avg(profit_margin), 2) as average_profit_margin,
    round(median(revenue_to_budget_ratio), 2) as median_revenue_to_budget_ratio,
    round(median(profit_margin), 2) as median_profit_margin
from movie_genre
group by genre_name, release_year
order by release_year, average_revenue_to_budget_ratio desc nulls last