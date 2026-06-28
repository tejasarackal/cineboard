with credits as (
    select movie_id, cast_list from {{ ref('stg_credits') }}
),
cast_members as (
    select
        c.movie_id,
        f.value:id::int as cast_id,
        f.value:name::string as cast_name,
        f.value:character::string as cast_character,
        f.value:order::int as cast_order,
        f.value:adult::boolean as cast_adult,
        f.value:gender::int as cast_gender,
        f.value:known_for_department::string as cast_known_for_department,
        f.value:popularity::float as cast_popularity,
        f.value:credit_id::string as cast_credit_id,
        f.value:department::string as cast_department,
        f.value:job::string as cast_job
    from credits as c
    cross join lateral flatten(input => c.cast_list) as f
)
select
    cm.movie_id,
    cm.cast_id as person_id,
    cm.cast_name as person_name,
    cm.cast_character as character,
    cm.cast_adult as adult,
    cm.cast_gender as gender,
    coalesce(cm.cast_known_for_department, cm.cast_department)  as department,
    cm.cast_popularity as popularity,
    cm.cast_credit_id as credit_id,
    cm.cast_job as job
from cast_members as cm
qualify row_number() over (partition by cm.movie_id order by cm.cast_popularity::number desc, cast_order::number asc) <= {{ var('cast_top_n') }}