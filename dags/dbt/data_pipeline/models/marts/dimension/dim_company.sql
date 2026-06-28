select distinct
    company_id,
    company_name,
    origin_country
from {{ ref('int_movie_company') }}