select distinct 
    genre_id,
    genre_name
from {{ ref('int_movie_genre') }}   