with movies as (
    select * from {{ ref('stg_movie_details') }}
)
select
    m.movie_id,
    m.title,
    m.original_title,
    m.original_language,
    m.status,
    m.release_date,
    m.runtime_min,
    m.budget,
    m.revenue,
    m.vote_average,
    (m.budget is not null and m.revenue is not null) as has_financial_data,
    case
        when m.budget is not null and m.revenue is not null then (m.revenue - m.budget) * 1.0 / nullif(m.budget, 0) 
    end as profit_margin,
    case
        when m.budget is not null and m.revenue is not null then m.revenue * 1.0 / nullif(m.budget, 0)
    end as revenue_to_budget_ratio,
    case
        when m.budget is not null and m.revenue is not null then m.revenue - m.budget
    end as profit,
    m.vote_count,
    m.popularity,
    m.overview,  
    m.video,
    m.adult,
    m.imdb_id,
    m.ingested_at
from movies as m
{% if is_incremental() %}
    where ingested_at > (select coalesce(max(ingested_at), '{{ var('historic_start_date') }}'::date) from {{ this }})
{% endif %}