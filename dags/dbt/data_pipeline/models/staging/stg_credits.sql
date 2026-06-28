with source as (
    select * from {{ source('tmdb', 'raw_credits') }}
)
select
    raw_payload:id::int as movie_id,
    raw_payload:cast::variant as cast_list,
    raw_payload:crew::variant as crew_list,
    ingested_at
from source
qualify row_number() over (partition by movie_id order by ingested_at desc) = 1