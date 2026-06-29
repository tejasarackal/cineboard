select distinct
    movie_id,
    company_id
from {{ ref('int_movie_company') }}