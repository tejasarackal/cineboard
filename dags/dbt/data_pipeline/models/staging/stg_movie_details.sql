with source as (
  select * from {{ source('tmdb', 'raw_movie_details') }}
)
select
  raw_payload:id::int as movie_id,
  raw_payload:title::string as title,
  raw_payload:original_name::string as original_name,
  raw_payload:original_title::string as original_title,
  raw_payload:original_language::string as original_language,
  raw_payload:status::string as status,
  raw_payload:release_date::date as release_date,
  raw_payload:runtime::int as runtime_min,
  nullif(raw_payload:budget::number, 0) as budget,
  nullif(raw_payload:revenue::number, 0) as revenue,
  raw_payload:vote_average::number(4,2) as vote_average,
  raw_payload:vote_count::int as vote_count,
  raw_payload:popularity::float as popularity,
  raw_payload:overview::string as overview,
  raw_payload:video::boolean as video,
  raw_payload:adult::boolean as adult,
  raw_payload:imdb_id::string as imdb_id,
  raw_payload:belongs_to_collection::variant as movie_belongs_to_collection,
  ingested_at
from source
qualify row_number() over (partition by movie_id order by ingested_at desc) = 1