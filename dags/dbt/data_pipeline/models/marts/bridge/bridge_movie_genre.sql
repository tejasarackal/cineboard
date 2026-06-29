select distinct
    movie_id,
    genre_id
from {{ ref('int_movie_genre') }}