select distinct
    movie_id,
    person_id,
    job
from {{ ref('int_movie_director') }}