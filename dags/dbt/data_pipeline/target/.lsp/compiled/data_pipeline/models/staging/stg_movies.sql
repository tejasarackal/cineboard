SELECT
  raw_payload:id::int as movie_id,
  raw_payload:title::string as movie_title,
  raw_payload:release_date::date as movie_release_date,
  raw_payload:genre_ids::array as movie_genre_ids,
  raw_payload:overview::string as movie_overview,
  raw_payload:poster_path::string as movie_poster_path,
  raw_payload:backdrop_path::string as movie_backdrop_path,
  raw_payload:vote_average::float as movie_vote_average,
  raw_payload:vote_count::int as movie_vote_count
FROM tesla_raw_db.tmdb.raw_movies