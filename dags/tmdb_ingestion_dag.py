import json
import logging
import os
import pandas as pd

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import dag, task, Variable
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import SnowflakeUserPasswordProfileMapping
from datetime import datetime, timedelta
from include.tmdb_api_helper import discover, details, credits

DBT_PROJECT_PATH = "/usr/local/airflow/dags/dbt/data_pipeline"
SHARED_DIR = "/tmp/shared/api_payloads"
PROFILE_CONFIG = ProfileConfig(
    profile_name="data_pipeline",
    target_name="dev",
    profile_mapping=SnowflakeUserPasswordProfileMapping(
        conn_id="snowflake_conn",
        profile_args={
            "database": "tesla_raw_db",
            "schema": "tmdb",
        },
    ),
)

PROJECT_CONFIG = ProjectConfig(DBT_PROJECT_PATH)
EXECUTION_CONFIG = ExecutionConfig(dbt_executable_path="/usr/local/airflow/dbt_venv/bin/dbt")

YEARS = Variable.get("tmdb_years", default="2018-2023")
MAX_MOVIES_PER_YEAR = int(Variable.get("tmdb_max_movies_per_year", default=100))
MAX_PAGES_PER_YEAR = int(Variable.get("tmdb_max_pages_per_year", default=100))
MAX_WORKERS = int(Variable.get("tmdb_max_workers", default=10))

log = logging.getLogger("airflow.task")

@dag(
    schedule="@daily",
    start_date=datetime(2026, 5, 27),
    catchup=False,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(seconds=10),
    },
    tags=["tmdb_ingestion_pipeline"],
)
def tmdb_ingestion_pipeline():

    def _write_payloads(records: list[dict], table_name: str):
        """Writes the records to a parquet file"""
        os.makedirs(SHARED_DIR, exist_ok=True)
        file_path = os.path.join(SHARED_DIR, f"{table_name}_{datetime.now().strftime('%Y%m%d')}.parquet")
        pd.DataFrame({"raw_payload": [json.dumps(record) for record in records]}).to_parquet(file_path)
        return file_path

    @task(task_id="extract_movies")
    def extract_movies() -> dict:
        """Extracts movies from TMDB API"""
        log.info(f"extract_movies: years={YEARS}, max/yr={MAX_MOVIES_PER_YEAR}")
        low, high = int(YEARS.split("-")[0]), int(YEARS.split("-")[1])
        years = list(range(low, high + 1))
        
        movies = []
        target_dict = {}

        for year in years:
            page, movies_catalogued = 1, 0
            while movies_catalogued < MAX_MOVIES_PER_YEAR:
                data = discover(year, page)
                results = data.get("results", [])
                if not results:
                    break
                
                # Edge case: if the number of movies found is less than the maximum number of movies per year, we need to break the loop
                movies_found = results[:MAX_MOVIES_PER_YEAR - movies_catalogued]
                movies.extend(movies_found)
                movies_catalogued += len(movies_found)

                # Handle the page limiter for API
                total_pages = min(data.get("total_pages", 1), MAX_PAGES_PER_YEAR)
                if page >= total_pages:
                    break
                page += 1

            log.info(f"extract_movies year={year}, pages={page}, movies={movies_catalogued}")
        
        target_dict["raw_movies"] = _write_payloads(movies, "raw_movies")
        target_dict["ids"] = sorted(set([movie["id"] for movie in movies]))
        log.info(f"extract_movies done: {len(movies)} movies, {len(target_dict['ids'])} unique ids, file={target_dict['raw_movies']}")

        return target_dict
    
    @task(task_id="extract_movie_details")
    def extract_movie_details(target_dict: dict) -> dict:
        """Extracts movie details from TMDB API"""
        ids = target_dict["ids"]
        log.info(f"extract_movie_details fan-out: fetching details+credits for {len(ids)} movies")

        movie_details, movie_credits = [], []
        for idx, movie_id in enumerate(ids, 1):
            movie_details.append(details(movie_id))
            movie_credits.append(credits(movie_id))
            if idx % 100 == 0:
                log.info("extract_movie_details fan-out: fetched %s/%s movies", idx, len(ids))

        log.info(f"extract_movie_details fan-out done: {len(movie_details)} details, {len(movie_credits)} credits")

        # Clean up the target dictionary to avoid confusing load task
        del target_dict["ids"]
        target_dict["raw_movie_details"] = _write_payloads(movie_details, "raw_movie_details")
        target_dict["raw_credits"] = _write_payloads(movie_credits, "raw_credits")

        return target_dict

    @task(task_id="load_tmdb_data")
    def load_tmdb_data(target_dict: dict):
        """Loads the extracted data into the target table"""
        
        for table_name, file_path in target_dict.items():

            hook = SnowflakeHook(snowflake_conn_id="snowflake_conn")
            stage_path = f"@tesla_raw_db.tmdb.api_payload/{table_name}"

            # PUT file into internal stage
            hook.run(f"PUT file://{file_path} {stage_path} AUTO_COMPRESS=TRUE OVERWRITE=TRUE;")

            # Copy the data from the stage to the target table
            copy_query =f"""
            COPY INTO tesla_raw_db.tmdb.{table_name} (raw_payload)
            FROM (SELECT parse_json($1:raw_payload) FROM {stage_path})
            FILE_FORMAT = (TYPE = PARQUET)
            """
            result = hook.run(copy_query, handler=lambda x: x.fetchall())
            log.info(f"load_tmdb_data loaded table={table_name} file={os.path.basename(file_path)} -> {result}")
            
            # Clean up the local file after successful load
            if os.path.exists(file_path):
                os.remove(file_path)

    # Orchestration and Task Dependencies
    movies = extract_movies()
    enriched = extract_movie_details(movies)
    load_raw = load_tmdb_data(enriched)

    transform_dbt_models = DbtTaskGroup(
        group_id="tmdb_dbt_models",
        project_config=PROJECT_CONFIG,
        profile_config=PROFILE_CONFIG,
        execution_config=EXECUTION_CONFIG,
    )

    movies >> enriched >> load_raw >> transform_dbt_models

tmdb_ingestion_dag = tmdb_ingestion_pipeline()