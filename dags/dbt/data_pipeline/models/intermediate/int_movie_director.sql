with credits as (
    select movie_id, crew_list from {{ ref('stg_credits') }}
)
select
    c.movie_id,
    f.value:id::int as person_id,
    f.value:name::string as person_name,
    f.value:job::string as job,
    f.value:department::string as department,
    f.value:known_for_department::string as known_for_department,
    f.value:popularity::float as popularity,
    f.value:gender::int as gender
from credits as c
cross join lateral flatten(input => c.crew_list) as f
where lower(f.value:job::string) = 'director'