with movie_details as (
    select
        movie_id,
        revenue,
        vote_average,
        vote_count
    from {{ ref('fact_movie') }}
),
global_mean as (
    select
        avg(vote_average) as global_mean_vote_average
    from movie_details
    where vote_count > {{ var('min_vote_count') }}
),
weighted_ratings as (
    select
        m.movie_id,
        m.revenue,
        (
            m.vote_average * m.vote_count + g.global_mean_vote_average * {{ var('min_vote_count') }}) 
            / (m.vote_count + {{ var('min_vote_count') }}
        ) as weighted_rating_score
    from movie_details as m cross join global_mean as g
),
cast_members as (
    select
        person_id,
        movie_id,
        'actor' as role_type
    from {{ ref('bridge_movie_cast') }}
    union all
    select
        person_id,
        movie_id,
        'director' as role_type
    from {{ ref('bridge_movie_director') }}
)
select
    p.person_id,
    dp.person_name,
    p.role_type,
    count(*) as movie_count,
    round(avg(w.weighted_rating_score), 2) as average_vote_rating,
    round(avg(w.revenue), 2) as average_revenue
from cast_members as p 
inner join {{ ref('dim_person') }} as dp on dp.person_id = p.person_id
inner join weighted_ratings as w on w.movie_id = p.movie_id
group by p.person_id, dp.person_name, p.role_type
having count(*) >= {{ var('min_films') }}
order by average_vote_rating desc nulls last
