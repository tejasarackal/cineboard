with observed as (
    select
        raw_payload:id::int as movie_id,
        ingested_at::date as snapshot_date,
        ingested_at::timestamp as ordering_ts,
        raw_payload:popularity::float as popularity,
        raw_payload:vote_average::number(4,2) as vote_average,
        raw_payload:vote_count::int as vote_count,
        nullif(raw_payload:revenue::int, 0) as revenue,
        false as is_synthetic
    from {{ source('tmdb', 'raw_movie_details') }}
)
{% if not is_incremental() %}
, synthetic as (
    select
        movie_id,
        snapshot_date,
        snapshot_date::timestamp as ordering_ts,
        popularity,
        vote_average,
        vote_count,
        revenue,
        true as is_synthetic
    from {{ ref('snapshot_seed') }}
)
{% endif %}
,combined as (
    select * from observed
    {% if not is_incremental() %}
        union all
        select * from synthetic
    {% endif %}
)
select
    movie_id,
    snapshot_date,
    popularity,
    vote_average,
    vote_count,
    revenue,
    is_synthetic
from combined
{% if is_incremental() %}
    where snapshot_date > (select coalesce(max(snapshot_date), '{{ var('historic_start_date') }}'::date) from {{ this }})
{% endif %}
qualify row_number() over (partition by movie_id, snapshot_date order by ordering_ts desc) = 1
