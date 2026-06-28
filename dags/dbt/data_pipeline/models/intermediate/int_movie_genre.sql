with movies as (
    select * from {{ ref('stg_movie_details') }}
)
select
    m.movie_id,
    g.value:id::int as genre_id,
    g.value:name::string as genre_name
from movies as m
cross join lateral flatten(input => m.genres) as g