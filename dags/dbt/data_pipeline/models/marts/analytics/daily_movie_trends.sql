with daily_movies as (
    select * from {{ ref('fact_movie_snapshot') }}
),
movies as (
    select * from {{ ref('fact_movie') }}
)
select
    m.movie_id,
    d.snapshot_date,
    m.title,
    m.budget,
    m.popularity as latest_popularity,
    d.popularity,
    d.vote_average,
    d.vote_count,
    d.revenue,
    d.is_synthetic
from movies as m
inner join daily_movies as d on m.movie_id = d.movie_id
where m.vote_count > {{ var('min_vote_count') }}
qualify dense_rank() over (order by latest_popularity desc) <= {{ var('top_n_movies') }}