-- created_at: 2026-06-28T10:25:43.727094+00:00
-- finished_at: 2026-06-28T10:25:44.063903+00:00
-- elapsed: 336ms
-- outcome: success
-- dialect: snowflake
-- node_id: test.data_pipeline.generic_non_negative_stg_movie_details_movie_revenue.6666fb532c
-- query_id: 01c55971-0106-2ee4-000f-0672000533ba
-- desc: execute adapter call
select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
SELECT
    *
FROM tesla_staging_db.cinema.stg_movie_details
WHERE movie_revenue < 0

  
  
      
    ) dbt_internal_test
/* {"app": "dbt", "dbt_version": "2.0.0", "node_id": "test.data_pipeline.generic_non_negative_stg_movie_details_movie_revenue.6666fb532c", "profile_name": "data_pipeline", "target_name": "dev"} */;
-- created_at: 2026-06-28T10:25:43.712444+00:00
-- finished_at: 2026-06-28T10:25:44.063904+00:00
-- elapsed: 351ms
-- outcome: success
-- dialect: snowflake
-- node_id: test.data_pipeline.not_null_stg_movies_movie_release_date.5edf5187f8
-- query_id: 01c55971-0106-2ee4-000f-0672000533b6
-- desc: execute adapter call
select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select movie_release_date
from tesla_staging_db.cinema.stg_movies
where movie_release_date is null



  
  
      
    ) dbt_internal_test
/* {"app": "dbt", "dbt_version": "2.0.0", "node_id": "test.data_pipeline.not_null_stg_movies_movie_release_date.5edf5187f8", "profile_name": "data_pipeline", "target_name": "dev"} */;
-- created_at: 2026-06-28T10:25:43.842260+00:00
-- finished_at: 2026-06-28T10:25:44.175620+00:00
-- elapsed: 333ms
-- outcome: success
-- dialect: snowflake
-- node_id: test.data_pipeline.unique_stg_movies_movie_id.51c7c15c78
-- query_id: 01c55971-0106-2ddf-000f-06720004d432
-- desc: execute adapter call
select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    movie_id as unique_field,
    count(*) as n_records

from tesla_staging_db.cinema.stg_movies
where movie_id is not null
group by movie_id
having count(*) > 1



  
  
      
    ) dbt_internal_test
/* {"app": "dbt", "dbt_version": "2.0.0", "node_id": "test.data_pipeline.unique_stg_movies_movie_id.51c7c15c78", "profile_name": "data_pipeline", "target_name": "dev"} */;
-- created_at: 2026-06-28T10:25:43.699502+00:00
-- finished_at: 2026-06-28T10:25:44.177542+00:00
-- elapsed: 478ms
-- outcome: success
-- dialect: snowflake
-- node_id: test.data_pipeline.relationships_stg_movie_details_movie_id__movie_id__ref_stg_movies_.95cf21905c
-- query_id: 01c55971-0106-2f44-000f-067200055022
-- desc: execute adapter call
select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select movie_id as from_field
    from tesla_staging_db.cinema.stg_movie_details
    where movie_id is not null
),

parent as (
    select movie_id as to_field
    from tesla_staging_db.cinema.stg_movies
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test
/* {"app": "dbt", "dbt_version": "2.0.0", "node_id": "test.data_pipeline.relationships_stg_movie_details_movie_id__movie_id__ref_stg_movies_.95cf21905c", "profile_name": "data_pipeline", "target_name": "dev"} */;
-- created_at: 2026-06-28T10:25:43.856772+00:00
-- finished_at: 2026-06-28T10:25:44.244679+00:00
-- elapsed: 387ms
-- outcome: success
-- dialect: snowflake
-- node_id: test.data_pipeline.not_null_stg_movies_movie_id.543dfa639e
-- query_id: 01c55971-0106-2ec2-000f-0672000513c6
-- desc: execute adapter call
select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select movie_id
from tesla_staging_db.cinema.stg_movies
where movie_id is null



  
  
      
    ) dbt_internal_test
/* {"app": "dbt", "dbt_version": "2.0.0", "node_id": "test.data_pipeline.not_null_stg_movies_movie_id.543dfa639e", "profile_name": "data_pipeline", "target_name": "dev"} */;
