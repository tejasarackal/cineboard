select
    movie_id,
    person_id,
    person_name,
    character as popular_character,
    popularity
from {{ ref('int_movie_cast') }}
qualify row_number() over (partition by movie_id, person_id order by popularity desc) = 1