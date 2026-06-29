with movie_genres as (
    select
        b.movie_id,
        g.genre_id,
        g.genre_name,
        extract(year from m.release_date) as release_year,
        extract(month from m.release_date) as release_month,
        m.popularity
    from {{ ref('bridge_movie_genre') }} as b
    inner join {{ ref('dim_genre') }} as g on b.genre_id = g.genre_id
    inner join {{ ref('fact_movie') }} as m on b.movie_id = m.movie_id
    where m.release_date is not null
)
select
    genre_name,
    release_year,
    release_month,
    round(avg(popularity), 2) as average_popularity
from movie_genres
group by genre_name, release_year, release_month
order by genre_name, release_year, release_month