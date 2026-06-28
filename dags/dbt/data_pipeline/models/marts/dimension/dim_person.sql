with people as (
    select 
        person_id,
        person_name,
        coalesce(job, department) as job,
        department,
        popularity,
        gender
    from {{ ref('int_movie_cast') }}
    union
    select
        person_id,
        person_name,
        job,
        department,
        popularity,
        gender
    from {{ ref('int_movie_director') }}
)
select distinct
    person_id,
    person_name,
    job,
    department,
    popularity,
    gender
from people
qualify row_number() over (partition by person_id order by popularity desc, department desc) = 1