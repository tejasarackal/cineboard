with movies as (
    select movie_id, production_companies from {{ ref('stg_movie_details') }}
)
select
    m.movie_id,
    c.value:id::int as company_id,
    c.value:name::string as company_name,
    c.value:origin_country::string as origin_country
from movies as m
cross join lateral flatten(input => m.production_companies) as c