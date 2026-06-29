-- one-time generator for seeds/snapshot_seed.csv
with movies_now as (
    select
        raw_payload:id::int as movie_id,
        raw_payload:popularity::float as cur_popularity,
        raw_payload:vote_average::number(4,2) as cur_vote_average,
        raw_payload:vote_count::int as cur_vote_count,
        nullif(raw_payload:revenue::int, 0) as cur_revenue
    from {{ source('tmdb', 'raw_movie_details') }}
    qualify row_number() over (partition by movie_id order by ingested_at desc) = 1
),

date_spine as (
    {{ dbt_utils.date_spine(
        datepart="month",
        start_date="dateadd(month, -6, date_trunc('month', current_date))",
        end_date="dateadd(month, -1, date_trunc('month', current_date))"
    ) }}
),

periods as (
    select
        date_month::date as snapshot_date,
        datediff('month', date_month, date_trunc('month', current_date)) as months_ago
    from date_spine
),

generated as (
    select
        m.movie_id,
        p.snapshot_date,
        p.months_ago,
        (abs(hash(m.movie_id)) % 1000) / 1000.0 as phase,
        (abs(hash(m.movie_id, p.months_ago)) % 1000) / 1000.0 as noise,
        (abs(hash(m.movie_id, p.months_ago, 7)) % 100) as spike_bucket,
        m.cur_popularity, 
        m.cur_vote_average, 
        m.cur_vote_count, 
        m.cur_revenue
    from movies_now as m
    cross join periods as p
)

select
    movie_id,
    snapshot_date,
    round(greatest(0,
        cur_popularity
        * (0.70 + 0.45 * sin(2 * pi() * (months_ago / 6.0 + phase)))
        * (0.90 + 0.20 * noise)
        * case when spike_bucket < 8 then 1.6 + noise else 1 end
    ), 3) as popularity,
    least(10, greatest(0,
        round(cur_vote_average + (noise - 0.5) * 0.15 - 0.02 * months_ago, 2)
    )) as vote_average,
    round(greatest(0,
        cur_vote_count * (1 - 0.004 * months_ago) * (0.998 + 0.004 * noise)
    ))::int  as vote_count,
    round(cur_revenue * (0.997 + 0.006 * noise))::int as revenue
from generated
where cur_popularity is not null
order by movie_id, snapshot_date
